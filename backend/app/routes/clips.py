"""Routes API pour la gestion des clips."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.database.crud import (
    get_vod_by_twitch_id,
    get_vod_highlights,
    create_highlight,
    create_clip,
    get_user_clips,
    update_vod_status,
)
from app.pipeline import ClipPipeline, PipelineProgress

router = APIRouter()


class ProcessVODRequest(BaseModel):
    """Requête de traitement d'une VOD."""
    vod_id: int
    max_clips: int = 5
    add_subtitles: bool = True
    subtitle_style: str = "modern"


class PublishRequest(BaseModel):
    """Requête de publication."""
    clip_id: int
    platforms: list[str]
    youtube_title: Optional[str] = None
    youtube_description: Optional[str] = None
    instagram_caption: Optional[str] = None


# État des jobs en cours
processing_jobs: dict[int, PipelineProgress] = {}


@router.post("/process")
async def process_vod(
    request: ProcessVODRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Lance le traitement d'une VOD pour générer des clips.
    
    Le traitement est effectué en arrière-plan.
    """
    from sqlalchemy import select
    from app.database.models import VOD
    
    # Récupérer la VOD
    result = await db.execute(select(VOD).where(VOD.id == request.vod_id))
    vod = result.scalar_one_or_none()
    
    if not vod:
        raise HTTPException(status_code=404, detail="VOD non trouvée")
    
    if vod.status == "processing":
        raise HTTPException(status_code=400, detail="VOD déjà en cours de traitement")
    
    # Mettre à jour le statut
    await update_vod_status(db, vod.id, "processing")
    
    # Lancer le traitement en arrière-plan
    background_tasks.add_task(
        _process_vod_background,
        vod_id=vod.id,
        twitch_vod_id=vod.twitch_vod_id,
        twitch_url=vod.twitch_url,
        max_clips=request.max_clips,
        add_subtitles=request.add_subtitles,
        subtitle_style=request.subtitle_style,
    )
    
    return {
        "message": "Traitement lancé",
        "vod_id": vod.id,
        "status": "processing",
    }


async def _process_vod_background(
    vod_id: int,
    twitch_vod_id: str,
    twitch_url: str,
    max_clips: int,
    add_subtitles: bool,
    subtitle_style: str,
):
    """Traitement en arrière-plan d'une VOD."""
    from app.database import async_session_maker
    
    def progress_callback(progress: PipelineProgress):
        processing_jobs[vod_id] = progress
    
    try:
        pipeline = ClipPipeline(
            add_subtitles=add_subtitles,
            subtitle_style=subtitle_style,
            max_clips=max_clips,
        )
        
        clips = await pipeline.process_vod(
            twitch_url,
            twitch_vod_id,
            progress_callback,
        )
        
        # Sauvegarder les clips en base
        async with async_session_maker() as db:
            for clip in clips:
                # Créer le highlight
                highlight = await create_highlight(
                    db,
                    vod_id=vod_id,
                    start_time=clip.highlight.start_time,
                    end_time=clip.highlight.end_time,
                    duration=clip.highlight.duration,
                    category=clip.highlight.category,
                    score=clip.highlight.combined_score,
                    transcript_excerpt=clip.highlight.transcript_excerpt,
                    audio_score=clip.highlight.audio_score,
                    llm_score=clip.highlight.llm_score,
                )
                
                # Créer le clip
                await create_clip(
                    db,
                    vod_id=vod_id,
                    highlight_id=highlight.id,
                    title=clip.title,
                    description=clip.description,
                    local_path=str(clip.path),
                    thumbnail_path=str(clip.thumbnail_path) if clip.thumbnail_path else None,
                    duration=clip.duration,
                    has_subtitles=add_subtitles,
                )
            
            await update_vod_status(db, vod_id, "completed")
    
    except Exception as e:
        async with async_session_maker() as db:
            await update_vod_status(db, vod_id, "error")
        
        processing_jobs[vod_id] = PipelineProgress(
            stage="error",
            progress=0,
            message=str(e),
        )
    
    finally:
        # Nettoyer après un délai
        import asyncio
        await asyncio.sleep(60)
        processing_jobs.pop(vod_id, None)


@router.get("/process/{vod_id}/status")
async def get_processing_status(vod_id: int):
    """Récupère le statut de traitement d'une VOD."""
    if vod_id in processing_jobs:
        progress = processing_jobs[vod_id]
        return {
            "status": "processing",
            "stage": progress.stage,
            "progress": progress.progress,
            "message": progress.message,
        }
    
    return {"status": "idle"}


@router.get("/user/{user_id}")
async def get_clips(
    user_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Récupère les clips d'un utilisateur."""
    clips = await get_user_clips(db, user_id, limit)
    
    return {
        "clips": [
            {
                "id": clip.id,
                "title": clip.title,
                "description": clip.description,
                "duration": clip.duration,
                "local_path": clip.local_path,
                "thumbnail_path": clip.thumbnail_path,
                "has_subtitles": clip.has_subtitles,
                "youtube_url": clip.youtube_url,
                "instagram_url": clip.instagram_url,
                "status": clip.status,
                "created_at": clip.created_at.isoformat(),
            }
            for clip in clips
        ],
    }


@router.post("/publish")
async def publish_clip(
    request: PublishRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Publie un clip sur les plateformes sélectionnées."""
    from sqlalchemy import select
    from app.database.models import Clip
    
    result = await db.execute(select(Clip).where(Clip.id == request.clip_id))
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip non trouvé")
    
    results = {}
    
    if "youtube" in request.platforms:
        from app.publishers.youtube import upload_to_youtube
        
        title = request.youtube_title or clip.title
        description = request.youtube_description or clip.description
        
        try:
            yt_result = upload_to_youtube(
                Path(clip.local_path),
                title=title,
                description=description,
            )
            results["youtube"] = yt_result
            
            # Mettre à jour le clip
            clip.youtube_video_id = yt_result["video_id"]
            clip.youtube_url = yt_result["url"]
            await db.commit()
            
        except Exception as e:
            results["youtube"] = {"error": str(e)}
    
    if "instagram" in request.platforms:
        from app.publishers.instagram import upload_to_instagram
        
        caption = request.instagram_caption or clip.title
        
        try:
            ig_result = upload_to_instagram(
                Path(clip.local_path),
                caption=caption,
            )
            results["instagram"] = ig_result
            
            clip.instagram_media_id = ig_result["media_id"]
            clip.instagram_url = ig_result.get("url")
            await db.commit()
            
        except Exception as e:
            results["instagram"] = {"error": str(e)}
    
    return {"results": results}

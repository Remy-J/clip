"""API Twitch - Récupération des VODs."""

from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.database.models import User
from app.database.crud import get_user_vods, create_vod, get_vod_by_twitch_id
from app.twitch.auth import refresh_twitch_token

router = APIRouter()

TWITCH_HELIX_URL = "https://api.twitch.tv/helix"


def parse_duration(duration_str: str) -> int:
    """Convertit une durée Twitch (ex: '3h2m1s') en secondes."""
    import re

    total_seconds = 0
    patterns = [
        (r"(\d+)h", 3600),
        (r"(\d+)m", 60),
        (r"(\d+)s", 1),
    ]

    for pattern, multiplier in patterns:
        match = re.search(pattern, duration_str)
        if match:
            total_seconds += int(match.group(1)) * multiplier

    return total_seconds


@router.get("/vods")
async def get_vods(
    user_id: int,
    first: int = Query(20, ge=1, le=100),
    after: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Récupère les VODs d'un utilisateur depuis Twitch."""
    settings = get_settings()

    # Récupérer le token
    access_token = await refresh_twitch_token(db, user_id)

    # Récupérer l'utilisateur pour son ID Twitch
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Appeler l'API Twitch
    async with httpx.AsyncClient() as client:
        params = {
            "user_id": user.twitch_id,
            "first": first,
            "type": "archive",
        }
        if after:
            params["after"] = after

        response = await client.get(
            f"{TWITCH_HELIX_URL}/videos",
            params=params,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Client-Id": settings.twitch_client_id,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur API Twitch: {response.text}"
            )

        data = response.json()
        vods = []

        for video in data.get("data", []):
            # Vérifier si la VOD existe déjà en base
            existing_vod = await get_vod_by_twitch_id(db, video["id"])

            if not existing_vod:
                # Créer la VOD en base
                vod = await create_vod(
                    db=db,
                    user_id=user.id,
                    twitch_vod_id=video["id"],
                    title=video["title"],
                    description=video.get("description"),
                    duration_seconds=parse_duration(video["duration"]),
                    view_count=video["view_count"],
                    language=video.get("language", "fr"),
                    thumbnail_url=video["thumbnail_url"].replace("%{width}", "320").replace("%{height}", "180"),
                    twitch_url=video["url"],
                    created_at_twitch=datetime.fromisoformat(video["created_at"].replace("Z", "+00:00")),
                    published_at_twitch=datetime.fromisoformat(video["published_at"].replace("Z", "+00:00")) if video.get("published_at") else None,
                )
                vods.append(vod)
            else:
                vods.append(existing_vod)

        return {
            "vods": [
                {
                    "id": vod.id,
                    "twitch_vod_id": vod.twitch_vod_id,
                    "title": vod.title,
                    "duration_seconds": vod.duration_seconds,
                    "duration_formatted": format_duration(vod.duration_seconds),
                    "view_count": vod.view_count,
                    "thumbnail_url": vod.thumbnail_url,
                    "twitch_url": vod.twitch_url,
                    "status": vod.status,
                    "created_at": vod.created_at_twitch.isoformat(),
                }
                for vod in vods
            ],
            "pagination": data.get("pagination", {}),
        }


@router.get("/vods/local")
async def get_local_vods(
    user_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Récupère les VODs stockées localement."""
    vods = await get_user_vods(db, user_id, limit)

    return {
        "vods": [
            {
                "id": vod.id,
                "twitch_vod_id": vod.twitch_vod_id,
                "title": vod.title,
                "duration_seconds": vod.duration_seconds,
                "duration_formatted": format_duration(vod.duration_seconds),
                "view_count": vod.view_count,
                "thumbnail_url": vod.thumbnail_url,
                "twitch_url": vod.twitch_url,
                "status": vod.status,
                "local_path": vod.local_path,
                "download_progress": vod.download_progress,
                "analysis_progress": vod.analysis_progress,
                "created_at": vod.created_at_twitch.isoformat(),
            }
            for vod in vods
        ],
    }


def format_duration(seconds: int) -> str:
    """Formate une durée en heures:minutes:secondes."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    elif minutes > 0:
        return f"{minutes}m{secs:02d}s"
    else:
        return f"{secs}s"

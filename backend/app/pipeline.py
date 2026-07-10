"""Pipeline principal - Orchestre le processus complet de création de clips."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from app.config import get_settings
from app.twitch.downloader import download_vod
from app.analysis.transcriber import transcribe_video, Transcript
from app.analysis.detector import HighlightDetector, DetectedHighlight
from app.video.clipper import cut_clip, generate_thumbnail
from app.video.formatter import format_vertical
from app.video.subtitles import create_styled_subtitles


@dataclass
class PipelineProgress:
    """État de progression du pipeline."""
    stage: str
    progress: float
    message: str


@dataclass 
class GeneratedClip:
    """Clip généré par le pipeline."""
    path: Path
    thumbnail_path: Optional[Path]
    title: str
    description: str
    category: str
    duration: float
    highlight: DetectedHighlight


class ClipPipeline:
    """
    Pipeline complet de création de clips.
    
    Étapes:
    1. Télécharger la VOD (si nécessaire)
    2. Transcrire avec Whisper
    3. Détecter les highlights (audio + LLM)
    4. Découper les clips
    5. Formater en vertical (9:16)
    6. Ajouter les sous-titres
    """
    
    def __init__(
        self,
        add_subtitles: bool = True,
        subtitle_style: str = "modern",
        max_clips: int = 5,
        min_score: float = 0.5,
    ):
        """
        Args:
            add_subtitles: Ajouter des sous-titres automatiques
            subtitle_style: Style des sous-titres (modern, classic, bold)
            max_clips: Nombre maximum de clips à générer
            min_score: Score minimum pour un highlight
        """
        self.add_subtitles = add_subtitles
        self.subtitle_style = subtitle_style
        self.max_clips = max_clips
        self.min_score = min_score
        self.settings = get_settings()
    
    async def process_vod(
        self,
        vod_url: str,
        vod_id: str,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
    ) -> list[GeneratedClip]:
        """
        Traite une VOD complète et génère des clips.
        
        Args:
            vod_url: URL de la VOD Twitch
            vod_id: Identifiant de la VOD
            progress_callback: Callback de progression
            
        Returns:
            Liste des clips générés
        """
        def report(stage: str, progress: float, message: str):
            if progress_callback:
                progress_callback(PipelineProgress(stage, progress, message))
        
        # Créer les répertoires
        vod_dir = self.settings.vods_dir / vod_id
        vod_dir.mkdir(parents=True, exist_ok=True)
        
        clips_dir = self.settings.clips_dir / vod_id
        clips_dir.mkdir(parents=True, exist_ok=True)
        
        transcript_path = self.settings.transcripts_dir / f"{vod_id}.json"
        
        # Étape 1: Télécharger la VOD
        report("download", 0, "Téléchargement de la VOD...")
        
        video_path = vod_dir / f"{vod_id}.mp4"
        
        if not video_path.exists():
            def download_progress(percent):
                report("download", percent / 100 * 0.3, f"Téléchargement: {percent:.1f}%")
            
            video_path = await download_vod(
                vod_url,
                vod_dir / vod_id,
                download_progress,
            )
        else:
            report("download", 0.3, "VOD déjà téléchargée")
        
        # Étape 2: Transcrire
        report("transcribe", 0.3, "Transcription en cours...")
        
        if transcript_path.exists():
            transcript = Transcript.load(transcript_path)
            report("transcribe", 0.5, "Transcription chargée depuis le cache")
        else:
            transcript = transcribe_video(video_path, transcript_path)
            report("transcribe", 0.5, "Transcription terminée")
        
        # Étape 3: Détecter les highlights
        report("analyze", 0.5, "Analyse des moments intéressants...")
        
        detector = HighlightDetector(min_combined_score=self.min_score)
        
        def analysis_progress(percent):
            report("analyze", 0.5 + percent / 100 * 0.2, f"Analyse: {percent}%")
        
        highlights = await detector.detect(
            video_path,
            transcript=transcript,
            max_highlights=self.max_clips,
            progress_callback=analysis_progress,
        )
        
        report("analyze", 0.7, f"{len(highlights)} moments détectés")
        
        # Étape 4-6: Créer les clips
        generated_clips = []
        
        for i, highlight in enumerate(highlights):
            clip_progress = 0.7 + (i / len(highlights)) * 0.3
            report(
                "clips",
                clip_progress,
                f"Création du clip {i + 1}/{len(highlights)}..."
            )
            
            clip = await self._create_clip(
                video_path=video_path,
                transcript=transcript,
                highlight=highlight,
                output_dir=clips_dir,
                clip_index=i + 1,
            )
            
            generated_clips.append(clip)
        
        report("done", 1.0, f"{len(generated_clips)} clips créés!")
        
        return generated_clips
    
    async def _create_clip(
        self,
        video_path: Path,
        transcript: Transcript,
        highlight: DetectedHighlight,
        output_dir: Path,
        clip_index: int,
    ) -> GeneratedClip:
        """Crée un clip à partir d'un highlight."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"clip_{clip_index}_{timestamp}"
        
        # Étape 4: Découper
        raw_clip_path = output_dir / f"{base_name}_raw.mp4"
        cut_clip(
            video_path,
            raw_clip_path,
            highlight.start_time,
            highlight.end_time,
            reencode=True,
        )
        
        # Étape 5: Formater en vertical
        vertical_clip_path = output_dir / f"{base_name}_vertical.mp4"
        format_vertical(
            raw_clip_path,
            vertical_clip_path,
            add_blur_background=True,
        )
        
        # Étape 6: Ajouter sous-titres
        if self.add_subtitles:
            final_clip_path = output_dir / f"{base_name}.mp4"
            create_styled_subtitles(
                transcript,
                vertical_clip_path,
                final_clip_path,
                start_offset=highlight.start_time,
                end_offset=highlight.end_time,
                style=self.subtitle_style,
            )
            # Nettoyer les fichiers intermédiaires
            raw_clip_path.unlink(missing_ok=True)
            vertical_clip_path.unlink(missing_ok=True)
        else:
            final_clip_path = vertical_clip_path
            raw_clip_path.unlink(missing_ok=True)
        
        # Générer la miniature
        thumbnail_path = output_dir / f"{base_name}_thumb.jpg"
        generate_thumbnail(final_clip_path, thumbnail_path)
        
        # Générer titre et description
        title = highlight.suggested_title or f"Moment {highlight.category}"
        description = (
            f"{highlight.reason}\n\n"
            f"Catégorie: {highlight.category}\n"
            f"Score: {highlight.combined_score:.2f}"
        )
        
        return GeneratedClip(
            path=final_clip_path,
            thumbnail_path=thumbnail_path,
            title=title,
            description=description,
            category=highlight.category,
            duration=highlight.duration,
            highlight=highlight,
        )


async def process_vod_to_clips(
    vod_url: str,
    vod_id: str,
    max_clips: int = 5,
    add_subtitles: bool = True,
) -> list[GeneratedClip]:
    """
    Fonction utilitaire pour traiter une VOD.
    
    Args:
        vod_url: URL de la VOD Twitch
        vod_id: Identifiant de la VOD
        max_clips: Nombre maximum de clips
        add_subtitles: Ajouter des sous-titres
        
    Returns:
        Liste des clips générés
    """
    pipeline = ClipPipeline(
        add_subtitles=add_subtitles,
        max_clips=max_clips,
    )
    
    return await pipeline.process_vod(vod_url, vod_id)

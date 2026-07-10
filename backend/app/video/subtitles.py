"""Génération et incrustation de sous-titres."""

import subprocess
from pathlib import Path
from typing import Optional

from app.analysis.transcriber import Transcript, TranscriptSegment


def generate_srt(
    transcript: Transcript,
    output_path: Path,
    start_offset: float = 0.0,
    end_offset: Optional[float] = None,
) -> Path:
    """
    Génère un fichier SRT à partir d'une transcription.
    
    Args:
        transcript: Transcription avec segments
        output_path: Chemin de sortie pour le fichier SRT
        start_offset: Décalage de début (pour clips découpés)
        end_offset: Fin de la section (optionnel)
        
    Returns:
        Chemin du fichier SRT
    """
    def format_timestamp(seconds: float) -> str:
        """Formate un timestamp en format SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    srt_lines = []
    subtitle_index = 1
    
    for segment in transcript.segments:
        # Ajuster les timestamps
        seg_start = segment.start - start_offset
        seg_end = segment.end - start_offset
        
        # Ignorer les segments hors de la plage
        if seg_start < 0:
            continue
        if end_offset and seg_end > end_offset - start_offset:
            continue
        
        # Diviser les segments trop longs
        text = segment.text.strip()
        if not text:
            continue
        
        # Max ~40 caractères par ligne, 2 lignes max
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 40:
                if len(current_line) > 1:
                    lines.append(" ".join(current_line[:-1]))
                    current_line = [word]
                else:
                    lines.append(" ".join(current_line))
                    current_line = []
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Limiter à 2 lignes
        if len(lines) > 2:
            lines = [" ".join(lines[:len(lines)//2]), " ".join(lines[len(lines)//2:])]
        
        formatted_text = "\n".join(lines)
        
        srt_lines.append(f"{subtitle_index}")
        srt_lines.append(f"{format_timestamp(seg_start)} --> {format_timestamp(seg_end)}")
        srt_lines.append(formatted_text)
        srt_lines.append("")
        
        subtitle_index += 1
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    
    return output_path


def burn_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    font_size: int = 24,
    font_color: str = "white",
    outline_color: str = "black",
    outline_width: int = 2,
    position: str = "bottom",
) -> Path:
    """
    Incruste les sous-titres dans une vidéo (hardcoded).
    
    Args:
        video_path: Chemin vers la vidéo
        srt_path: Chemin vers le fichier SRT
        output_path: Chemin de sortie
        font_size: Taille de police
        font_color: Couleur du texte
        outline_color: Couleur du contour
        outline_width: Épaisseur du contour
        position: Position (bottom, center, top)
        
    Returns:
        Chemin de la vidéo avec sous-titres
    """
    # Position verticale
    margin_v = {
        "bottom": 50,
        "center": 0,
        "top": 50,
    }.get(position, 50)
    
    alignment = {
        "bottom": 2,
        "center": 10,
        "top": 6,
    }.get(position, 2)
    
    # Échapper le chemin pour FFmpeg (Windows)
    srt_path_escaped = str(srt_path).replace("\\", "/").replace(":", r"\:")
    
    subtitles_filter = (
        f"subtitles='{srt_path_escaped}':"
        f"force_style='FontSize={font_size},"
        f"PrimaryColour=&H{_color_to_ass(font_color)},"
        f"OutlineColour=&H{_color_to_ass(outline_color)},"
        f"Outline={outline_width},"
        f"Alignment={alignment},"
        f"MarginV={margin_v},"
        f"FontName=Arial'"
    )
    
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", subtitles_filter,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-y",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Erreur FFmpeg: {result.stderr}")
    
    return output_path


def _color_to_ass(color: str) -> str:
    """Convertit un nom de couleur en format ASS (AABBGGRR)."""
    colors = {
        "white": "00FFFFFF",
        "black": "00000000",
        "red": "000000FF",
        "green": "0000FF00",
        "blue": "00FF0000",
        "yellow": "0000FFFF",
    }
    return colors.get(color.lower(), "00FFFFFF")


def create_styled_subtitles(
    transcript: Transcript,
    video_path: Path,
    output_path: Path,
    start_offset: float = 0.0,
    end_offset: Optional[float] = None,
    style: str = "modern",
) -> Path:
    """
    Crée une vidéo avec sous-titres stylisés.
    
    Args:
        transcript: Transcription
        video_path: Vidéo source
        output_path: Chemin de sortie
        start_offset: Décalage de début
        end_offset: Fin (optionnel)
        style: Style de sous-titres (modern, classic, bold)
        
    Returns:
        Chemin de la vidéo avec sous-titres
    """
    styles = {
        "modern": {
            "font_size": 28,
            "font_color": "white",
            "outline_color": "black",
            "outline_width": 3,
            "position": "bottom",
        },
        "classic": {
            "font_size": 24,
            "font_color": "yellow",
            "outline_color": "black",
            "outline_width": 2,
            "position": "bottom",
        },
        "bold": {
            "font_size": 32,
            "font_color": "white",
            "outline_color": "black",
            "outline_width": 4,
            "position": "center",
        },
    }
    
    style_config = styles.get(style, styles["modern"])
    
    # Générer le SRT temporaire
    srt_path = output_path.with_suffix(".srt")
    generate_srt(transcript, srt_path, start_offset, end_offset)
    
    try:
        return burn_subtitles(
            video_path,
            srt_path,
            output_path,
            **style_config,
        )
    finally:
        # Nettoyer le fichier SRT temporaire
        if srt_path.exists():
            srt_path.unlink()

"""Découpage vidéo avec FFmpeg."""

import subprocess
from pathlib import Path
from typing import Optional


def cut_clip(
    input_path: Path,
    output_path: Path,
    start_time: float,
    end_time: float,
    reencode: bool = False,
) -> Path:
    """
    Découpe un segment de vidéo.
    
    Args:
        input_path: Chemin vers la vidéo source
        output_path: Chemin de sortie pour le clip
        start_time: Timestamp de début en secondes
        end_time: Timestamp de fin en secondes
        reencode: Si True, ré-encode la vidéo (plus lent mais plus précis)
        
    Returns:
        Chemin du clip créé
    """
    duration = end_time - start_time
    
    if reencode:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "23",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", str(input_path),
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-y",
            str(output_path),
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Erreur FFmpeg: {result.stderr}")
    
    return output_path


def get_video_info(video_path: Path) -> dict:
    """
    Récupère les informations d'une vidéo.
    
    Args:
        video_path: Chemin vers la vidéo
        
    Returns:
        Dictionnaire avec width, height, duration, fps, codec
    """
    import json
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Erreur ffprobe: {result.stderr}")
    
    data = json.loads(result.stdout)
    
    video_stream = next(
        (s for s in data.get("streams", []) if s["codec_type"] == "video"),
        None
    )
    
    if not video_stream:
        raise ValueError("Pas de flux vidéo trouvé")
    
    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    fps = int(fps_parts[0]) / int(fps_parts[1]) if len(fps_parts) == 2 else 30
    
    return {
        "width": int(video_stream.get("width", 1920)),
        "height": int(video_stream.get("height", 1080)),
        "duration": float(data.get("format", {}).get("duration", 0)),
        "fps": fps,
        "codec": video_stream.get("codec_name", "h264"),
    }


def generate_thumbnail(
    video_path: Path,
    output_path: Path,
    timestamp: Optional[float] = None,
) -> Path:
    """
    Génère une miniature à partir d'une vidéo.
    
    Args:
        video_path: Chemin vers la vidéo
        output_path: Chemin de sortie pour la miniature
        timestamp: Timestamp en secondes (défaut: 1 seconde)
        
    Returns:
        Chemin de la miniature
    """
    if timestamp is None:
        timestamp = 1.0
    
    cmd = [
        "ffmpeg",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        "-y",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Erreur FFmpeg: {result.stderr}")
    
    return output_path


def check_ffmpeg_installed() -> bool:
    """Vérifie si FFmpeg est installé."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

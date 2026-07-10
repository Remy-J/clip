"""Formatage vidéo pour Shorts/Reels (format vertical 9:16)."""

import subprocess
from pathlib import Path
from typing import Literal, Optional

from app.video.clipper import get_video_info


CropMode = Literal["center", "left", "right", "auto"]


def format_vertical(
    input_path: Path,
    output_path: Path,
    target_width: int = 1080,
    target_height: int = 1920,
    crop_mode: CropMode = "center",
    add_blur_background: bool = True,
) -> Path:
    """
    Convertit une vidéo horizontale en format vertical (9:16).
    
    Args:
        input_path: Chemin vers la vidéo source
        output_path: Chemin de sortie
        target_width: Largeur cible (défaut: 1080)
        target_height: Hauteur cible (défaut: 1920)
        crop_mode: Mode de crop (center, left, right, auto)
        add_blur_background: Ajoute un fond flouté si la vidéo ne remplit pas
        
    Returns:
        Chemin de la vidéo formatée
    """
    info = get_video_info(input_path)
    source_width = info["width"]
    source_height = info["height"]
    
    # Calculer le ratio
    source_ratio = source_width / source_height
    target_ratio = target_width / target_height
    
    if add_blur_background and source_ratio > target_ratio:
        # La vidéo est plus large que le format cible
        # On ajoute un fond flouté
        filter_complex = _create_blur_background_filter(
            source_width, source_height,
            target_width, target_height,
            crop_mode,
        )
    else:
        # Simple crop ou scale
        filter_complex = _create_simple_filter(
            source_width, source_height,
            target_width, target_height,
            crop_mode,
        )
    
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-r", "30",
        "-y",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Erreur FFmpeg: {result.stderr}")
    
    return output_path


def _create_blur_background_filter(
    sw: int, sh: int,
    tw: int, th: int,
    crop_mode: str,
) -> str:
    """
    Crée un filtre FFmpeg avec fond flouté.
    
    La vidéo principale est mise à l'échelle pour remplir la hauteur,
    avec un fond flouté et zoomé.
    """
    # Calculer la taille de la vidéo principale (remplir la hauteur)
    main_height = th
    main_width = int(sw * (th / sh))
    
    # Position X selon le mode
    if crop_mode == "left":
        x_pos = 0
    elif crop_mode == "right":
        x_pos = tw - main_width
    else:  # center
        x_pos = (tw - main_width) // 2
    
    filter_parts = [
        # Fond: scale + crop + blur
        f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=increase,"
        f"crop={tw}:{th},"
        f"boxblur=20:5[bg]",
        
        # Vidéo principale: scale pour remplir la hauteur
        f"[0:v]scale={main_width}:{main_height}[main]",
        
        # Overlay
        f"[bg][main]overlay={x_pos}:0[outv]",
    ]
    
    return ";".join(filter_parts)


def _create_simple_filter(
    sw: int, sh: int,
    tw: int, th: int,
    crop_mode: str,
) -> str:
    """
    Crée un filtre FFmpeg simple (scale + crop).
    """
    # Calculer les dimensions après scale
    scale_ratio = max(tw / sw, th / sh)
    scaled_w = int(sw * scale_ratio)
    scaled_h = int(sh * scale_ratio)
    
    # Position du crop
    if crop_mode == "left":
        crop_x = 0
    elif crop_mode == "right":
        crop_x = scaled_w - tw
    else:  # center ou auto
        crop_x = (scaled_w - tw) // 2
    
    crop_y = (scaled_h - th) // 2
    
    return (
        f"[0:v]scale={scaled_w}:{scaled_h},"
        f"crop={tw}:{th}:{crop_x}:{crop_y}[outv]"
    )


def format_for_platform(
    input_path: Path,
    output_path: Path,
    platform: Literal["youtube_shorts", "instagram_reels", "tiktok"],
) -> Path:
    """
    Formate une vidéo pour une plateforme spécifique.
    
    Args:
        input_path: Chemin vers la vidéo source
        output_path: Chemin de sortie
        platform: Plateforme cible
        
    Returns:
        Chemin de la vidéo formatée
    """
    platform_specs = {
        "youtube_shorts": {
            "width": 1080,
            "height": 1920,
            "max_duration": 60,
        },
        "instagram_reels": {
            "width": 1080,
            "height": 1920,
            "max_duration": 90,
        },
        "tiktok": {
            "width": 1080,
            "height": 1920,
            "max_duration": 180,
        },
    }
    
    specs = platform_specs.get(platform, platform_specs["youtube_shorts"])
    
    return format_vertical(
        input_path,
        output_path,
        target_width=specs["width"],
        target_height=specs["height"],
    )

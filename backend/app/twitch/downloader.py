"""Téléchargement des VODs Twitch."""

import asyncio
import subprocess
from pathlib import Path
from typing import Callable, Optional

from app.config import get_settings


async def download_vod(
    vod_url: str,
    output_path: Path,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Path:
    """
    Télécharge une VOD Twitch avec yt-dlp.

    Args:
        vod_url: URL de la VOD Twitch
        output_path: Chemin de sortie (sans extension)
        progress_callback: Fonction appelée avec le pourcentage de progression

    Returns:
        Chemin du fichier téléchargé
    """
    settings = get_settings()

    output_template = str(output_path.with_suffix(".%(ext)s"))

    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--newline",
        "--progress",
        "-f", "best[height<=1080]",
        "-o", output_template,
        vod_url,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    final_path = None

    while True:
        line = await process.stdout.readline()
        if not line:
            break

        line = line.decode().strip()

        # Parser la progression
        if "[download]" in line and "%" in line:
            try:
                percent_str = line.split("%")[0].split()[-1]
                percent = float(percent_str)
                if progress_callback:
                    await asyncio.get_event_loop().run_in_executor(
                        None, progress_callback, percent
                    )
            except (ValueError, IndexError):
                pass

        # Détecter le fichier de destination
        if "[download] Destination:" in line:
            final_path = Path(line.split("Destination:")[-1].strip())
        elif "has already been downloaded" in line:
            final_path = output_path.with_suffix(".mp4")

    await process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Erreur lors du téléchargement: code {process.returncode}")

    # Trouver le fichier téléchargé
    if final_path and final_path.exists():
        return final_path

    # Chercher le fichier avec différentes extensions
    for ext in [".mp4", ".mkv", ".webm", ".ts"]:
        potential_path = output_path.with_suffix(ext)
        if potential_path.exists():
            return potential_path

    raise FileNotFoundError(f"Fichier téléchargé introuvable: {output_path}")


async def get_vod_info(vod_url: str) -> dict:
    """
    Récupère les informations d'une VOD sans la télécharger.

    Args:
        vod_url: URL de la VOD Twitch

    Returns:
        Dictionnaire avec les informations de la VOD
    """
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "-j",
        vod_url,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Erreur yt-dlp: {stderr.decode()}")

    import json
    return json.loads(stdout.decode())


def check_ytdlp_installed() -> bool:
    """Vérifie si yt-dlp est installé."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

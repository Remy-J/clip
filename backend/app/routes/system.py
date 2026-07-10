"""Routes système - Vérification des dépendances."""

from fastapi import APIRouter

from app.config import get_settings
from app.video.clipper import check_ffmpeg_installed
from app.twitch.downloader import check_ytdlp_installed
from app.analysis.llm import check_ollama_available

router = APIRouter()


@router.get("/check")
async def check_dependencies():
    """
    Vérifie que toutes les dépendances sont installées et configurées.
    """
    settings = get_settings()
    
    checks = {
        "ffmpeg": {
            "installed": check_ffmpeg_installed(),
            "required": True,
            "install_cmd": "Télécharger depuis https://ffmpeg.org/download.html",
        },
        "yt_dlp": {
            "installed": check_ytdlp_installed(),
            "required": True,
            "install_cmd": "pip install yt-dlp",
        },
        "ollama": check_ollama_available(),
        "twitch_api": {
            "configured": bool(settings.twitch_client_id and settings.twitch_client_secret),
            "required": True,
            "help": "Configurez TWITCH_CLIENT_ID et TWITCH_CLIENT_SECRET dans .env",
        },
        "directories": {
            "data_dir": settings.data_dir.exists(),
            "vods_dir": settings.vods_dir.exists(),
            "clips_dir": settings.clips_dir.exists(),
            "transcripts_dir": settings.transcripts_dir.exists(),
        },
    }
    
    # Calculer le statut global
    all_ok = (
        checks["ffmpeg"]["installed"] and
        checks["yt_dlp"]["installed"] and
        checks["ollama"][0] and
        checks["twitch_api"]["configured"]
    )
    
    return {
        "status": "ok" if all_ok else "missing_dependencies",
        "checks": checks,
        "settings": {
            "whisper_model": settings.whisper_model,
            "ollama_model": settings.ollama_model,
            "clip_format": settings.clip_format,
        },
    }


@router.get("/setup-guide")
async def setup_guide():
    """
    Retourne un guide de configuration étape par étape.
    """
    return {
        "steps": [
            {
                "id": 1,
                "title": "Installer FFmpeg",
                "description": "FFmpeg est requis pour le traitement vidéo",
                "windows": [
                    "1. Télécharger depuis https://www.gyan.dev/ffmpeg/builds/",
                    "2. Extraire dans C:\\ffmpeg",
                    "3. Ajouter C:\\ffmpeg\\bin au PATH système",
                    "4. Redémarrer le terminal",
                ],
                "check_cmd": "ffmpeg -version",
            },
            {
                "id": 2,
                "title": "Installer Ollama",
                "description": "Ollama fait tourner les LLMs localement",
                "windows": [
                    "1. Télécharger depuis https://ollama.ai/download",
                    "2. Installer l'application",
                    "3. Lancer Ollama",
                    "4. Exécuter: ollama pull llama3.1:8b",
                ],
                "check_cmd": "ollama list",
            },
            {
                "id": 3,
                "title": "Configurer Twitch API",
                "description": "Nécessaire pour accéder à vos VODs",
                "steps": [
                    "1. Aller sur https://dev.twitch.tv/console",
                    "2. Se connecter avec votre compte Twitch",
                    "3. Cliquer sur 'Register Your Application'",
                    "4. Nom: Nexus, OAuth Redirect URL: http://localhost:8000/auth/twitch/callback",
                    "5. Catégorie: Application Integration",
                    "6. Copier Client ID et générer Client Secret",
                    "7. Ajouter dans le fichier .env",
                ],
            },
            {
                "id": 4,
                "title": "Configurer YouTube API (optionnel)",
                "description": "Pour publier automatiquement sur YouTube",
                "steps": [
                    "1. Aller sur https://console.cloud.google.com",
                    "2. Créer un nouveau projet",
                    "3. Activer YouTube Data API v3",
                    "4. Créer des identifiants OAuth 2.0",
                    "5. Télécharger le fichier credentials.json",
                    "6. Placer dans le dossier data/",
                ],
            },
            {
                "id": 5,
                "title": "Configurer Instagram (optionnel)",
                "description": "Pour publier automatiquement sur Instagram",
                "steps": [
                    "1. Convertir votre compte en compte Professionnel",
                    "2. Lier une page Facebook",
                    "3. La première connexion se fera via l'application",
                ],
            },
        ],
    }

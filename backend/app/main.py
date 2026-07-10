"""Point d'entrée principal de l'API FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.twitch.auth import router as twitch_auth_router
from app.twitch.api import router as twitch_api_router
from app.routes.clips import router as clips_router
from app.routes.system import router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    settings = get_settings()
    settings.setup_directories()
    await init_db()
    yield


app = FastAPI(
    title="Nexus",
    description="Application de création automatique de clips à partir de VODs Twitch",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(twitch_auth_router, prefix="/auth/twitch", tags=["Twitch Auth"])
app.include_router(twitch_api_router, prefix="/api/twitch", tags=["Twitch API"])
app.include_router(clips_router, prefix="/api/clips", tags=["Clips"])
app.include_router(system_router, prefix="/api/system", tags=["System"])


@app.get("/")
async def root():
    """Page d'accueil."""
    return {
        "app": "Nexus",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'application."""
    settings = get_settings()
    return {
        "status": "healthy",
        "twitch_configured": bool(settings.twitch_client_id),
        "youtube_configured": bool(settings.youtube_client_id),
        "ollama_host": settings.ollama_host,
        "whisper_model": settings.whisper_model,
    }

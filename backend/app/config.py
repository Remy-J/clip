"""Configuration de l'application."""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Paramètres de l'application."""

    # Application
    app_name: str = "Nexus"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "sqlite:///./data/nexus.db"

    # Data directories
    data_dir: Path = Path("./data")
    vods_dir: Path = Path("./data/vods")
    clips_dir: Path = Path("./data/clips")
    transcripts_dir: Path = Path("./data/transcripts")

    # Twitch
    twitch_client_id: str = ""
    twitch_client_secret: str = ""
    twitch_redirect_uri: str = "http://localhost:8000/auth/twitch/callback"

    # YouTube
    youtube_client_id: str = ""
    youtube_client_secret: str = ""

    # Instagram
    instagram_access_token: str = ""
    instagram_business_id: str = ""

    # Ollama (LLM local)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Whisper (transcription locale)
    whisper_model: str = "small"
    whisper_device: str = "auto"

    # Clip settings
    clip_min_duration: int = 15
    clip_max_duration: int = 60
    clip_format: str = "9:16"
    clip_resolution: tuple[int, int] = (1080, 1920)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def setup_directories(self) -> None:
        """Crée les répertoires de données s'ils n'existent pas."""
        for directory in [self.data_dir, self.vods_dir, self.clips_dir, self.transcripts_dir]:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance des paramètres (singleton)."""
    settings = Settings()
    settings.setup_directories()
    return settings

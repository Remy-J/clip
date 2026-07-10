"""Modèles de base de données SQLAlchemy."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Utilisateur (connecté via Twitch)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    twitch_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    twitch_login: Mapped[str] = mapped_column(String(100))
    twitch_display_name: Mapped[str] = mapped_column(String(100))
    twitch_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    twitch_profile_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Tokens Twitch
    twitch_access_token: Mapped[str] = mapped_column(Text)
    twitch_refresh_token: Mapped[str] = mapped_column(Text)
    twitch_token_expires_at: Mapped[datetime] = mapped_column(DateTime)

    # Tokens YouTube (optionnel)
    youtube_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Instagram (optionnel)
    instagram_session: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    vods: Mapped[list["VOD"]] = relationship("VOD", back_populates="user")


class VOD(Base):
    """VOD Twitch."""

    __tablename__ = "vods"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    twitch_vod_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str] = mapped_column(String(10), default="fr")
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    twitch_url: Mapped[str] = mapped_column(String(500))

    created_at_twitch: Mapped[datetime] = mapped_column(DateTime)
    published_at_twitch: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Statut de traitement
    status: Mapped[str] = mapped_column(String(50), default="pending")
    local_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    transcript_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Métadonnées de traitement
    download_progress: Mapped[float] = mapped_column(Float, default=0.0)
    analysis_progress: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="vods")
    clips: Mapped[list["Clip"]] = relationship("Clip", back_populates="vod")
    highlights: Mapped[list["Highlight"]] = relationship("Highlight", back_populates="vod")


class Highlight(Base):
    """Moment détecté dans une VOD."""

    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(primary_key=True)
    vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id"))

    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)

    # Analyse
    category: Mapped[str] = mapped_column(String(50))
    score: Mapped[float] = mapped_column(Float)
    transcript_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Scores détaillés
    audio_score: Mapped[float] = mapped_column(Float, default=0.0)
    llm_score: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    vod: Mapped["VOD"] = relationship("VOD", back_populates="highlights")
    clip: Mapped[Optional["Clip"]] = relationship("Clip", back_populates="highlight", uselist=False)


class Clip(Base):
    """Clip généré à partir d'un highlight."""

    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(primary_key=True)
    vod_id: Mapped[int] = mapped_column(ForeignKey("vods.id"))
    highlight_id: Mapped[Optional[int]] = mapped_column(ForeignKey("highlights.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    local_path: Mapped[str] = mapped_column(String(1000))
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    duration: Mapped[float] = mapped_column(Float)
    format: Mapped[str] = mapped_column(String(10), default="9:16")
    resolution: Mapped[str] = mapped_column(String(20), default="1080x1920")
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False)

    # Publication
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    youtube_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    instagram_media_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    instagram_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    instagram_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="created")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    vod: Mapped["VOD"] = relationship("VOD", back_populates="clips")
    highlight: Mapped[Optional["Highlight"]] = relationship("Highlight", back_populates="clip")

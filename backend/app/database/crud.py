"""Opérations CRUD pour la base de données."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, VOD, Highlight, Clip


# === Users ===

async def get_user_by_twitch_id(db: AsyncSession, twitch_id: str) -> Optional[User]:
    """Récupère un utilisateur par son ID Twitch."""
    result = await db.execute(select(User).where(User.twitch_id == twitch_id))
    return result.scalar_one_or_none()


async def create_or_update_user(
    db: AsyncSession,
    twitch_id: str,
    twitch_login: str,
    twitch_display_name: str,
    twitch_email: Optional[str],
    twitch_profile_image: Optional[str],
    access_token: str,
    refresh_token: str,
    expires_at: datetime,
) -> User:
    """Crée ou met à jour un utilisateur."""
    user = await get_user_by_twitch_id(db, twitch_id)

    if user:
        user.twitch_login = twitch_login
        user.twitch_display_name = twitch_display_name
        user.twitch_email = twitch_email
        user.twitch_profile_image = twitch_profile_image
        user.twitch_access_token = access_token
        user.twitch_refresh_token = refresh_token
        user.twitch_token_expires_at = expires_at
    else:
        user = User(
            twitch_id=twitch_id,
            twitch_login=twitch_login,
            twitch_display_name=twitch_display_name,
            twitch_email=twitch_email,
            twitch_profile_image=twitch_profile_image,
            twitch_access_token=access_token,
            twitch_refresh_token=refresh_token,
            twitch_token_expires_at=expires_at,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user


# === VODs ===

async def get_vod_by_twitch_id(db: AsyncSession, twitch_vod_id: str) -> Optional[VOD]:
    """Récupère une VOD par son ID Twitch."""
    result = await db.execute(select(VOD).where(VOD.twitch_vod_id == twitch_vod_id))
    return result.scalar_one_or_none()


async def get_user_vods(db: AsyncSession, user_id: int, limit: int = 50) -> list[VOD]:
    """Récupère les VODs d'un utilisateur."""
    result = await db.execute(
        select(VOD)
        .where(VOD.user_id == user_id)
        .order_by(VOD.created_at_twitch.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_vod(db: AsyncSession, user_id: int, **kwargs) -> VOD:
    """Crée une nouvelle VOD."""
    vod = VOD(user_id=user_id, **kwargs)
    db.add(vod)
    await db.commit()
    await db.refresh(vod)
    return vod


async def update_vod_status(db: AsyncSession, vod_id: int, status: str, **kwargs) -> VOD:
    """Met à jour le statut d'une VOD."""
    result = await db.execute(select(VOD).where(VOD.id == vod_id))
    vod = result.scalar_one()
    vod.status = status
    for key, value in kwargs.items():
        setattr(vod, key, value)
    await db.commit()
    await db.refresh(vod)
    return vod


# === Highlights ===

async def create_highlight(db: AsyncSession, vod_id: int, **kwargs) -> Highlight:
    """Crée un nouveau highlight."""
    highlight = Highlight(vod_id=vod_id, **kwargs)
    db.add(highlight)
    await db.commit()
    await db.refresh(highlight)
    return highlight


async def get_vod_highlights(db: AsyncSession, vod_id: int) -> list[Highlight]:
    """Récupère les highlights d'une VOD."""
    result = await db.execute(
        select(Highlight)
        .where(Highlight.vod_id == vod_id)
        .order_by(Highlight.score.desc())
    )
    return list(result.scalars().all())


# === Clips ===

async def create_clip(db: AsyncSession, vod_id: int, **kwargs) -> Clip:
    """Crée un nouveau clip."""
    clip = Clip(vod_id=vod_id, **kwargs)
    db.add(clip)
    await db.commit()
    await db.refresh(clip)
    return clip


async def get_user_clips(db: AsyncSession, user_id: int, limit: int = 50) -> list[Clip]:
    """Récupère les clips d'un utilisateur."""
    result = await db.execute(
        select(Clip)
        .join(VOD)
        .where(VOD.user_id == user_id)
        .order_by(Clip.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_clip_publication(
    db: AsyncSession,
    clip_id: int,
    platform: str,
    media_id: str,
    url: str,
) -> Clip:
    """Met à jour les informations de publication d'un clip."""
    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one()

    if platform == "youtube":
        clip.youtube_video_id = media_id
        clip.youtube_url = url
        clip.youtube_published_at = datetime.utcnow()
    elif platform == "instagram":
        clip.instagram_media_id = media_id
        clip.instagram_url = url
        clip.instagram_published_at = datetime.utcnow()

    clip.status = "published"
    await db.commit()
    await db.refresh(clip)
    return clip

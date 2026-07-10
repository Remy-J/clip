"""Authentification OAuth Twitch."""

from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.database.crud import create_or_update_user

router = APIRouter()

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
TWITCH_USERS_URL = "https://api.twitch.tv/helix/users"


@router.get("/login")
async def login():
    """Redirige vers la page de connexion Twitch."""
    settings = get_settings()

    if not settings.twitch_client_id:
        raise HTTPException(
            status_code=500,
            detail="Twitch Client ID non configuré. Voir PLAN.md pour la configuration."
        )

    params = {
        "client_id": settings.twitch_client_id,
        "redirect_uri": settings.twitch_redirect_uri,
        "response_type": "code",
        "scope": "user:read:email user:read:broadcast",
    }

    auth_url = f"{TWITCH_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Callback OAuth après connexion Twitch."""
    settings = get_settings()

    # Échanger le code contre un token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TWITCH_TOKEN_URL,
            data={
                "client_id": settings.twitch_client_id,
                "client_secret": settings.twitch_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.twitch_redirect_uri,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de l'échange du token: {token_response.text}"
            )

        token_data = token_response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Récupérer les informations utilisateur
        user_response = await client.get(
            TWITCH_USERS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Client-Id": settings.twitch_client_id,
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la récupération du profil: {user_response.text}"
            )

        user_data = user_response.json()["data"][0]

        # Créer ou mettre à jour l'utilisateur
        user = await create_or_update_user(
            db=db,
            twitch_id=user_data["id"],
            twitch_login=user_data["login"],
            twitch_display_name=user_data["display_name"],
            twitch_email=user_data.get("email"),
            twitch_profile_image=user_data.get("profile_image_url"),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        # Rediriger vers le frontend avec les données utilisateur
        import urllib.parse
        import json
        
        user_data = {
            "id": user.id,
            "twitch_id": user.twitch_id,
            "login": user.twitch_login,
            "display_name": user.twitch_display_name,
            "profile_image": user.twitch_profile_image,
        }
        
        encoded_user = urllib.parse.quote(json.dumps(user_data))
        
        return RedirectResponse(
            url=f"http://localhost:5173/?user={encoded_user}",
            status_code=302,
        )


async def refresh_twitch_token(db: AsyncSession, user_id: int) -> str:
    """Rafraîchit le token Twitch d'un utilisateur."""
    from app.database.models import User
    from sqlalchemy import select

    settings = get_settings()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Vérifier si le token a expiré
    if user.twitch_token_expires_at > datetime.utcnow():
        return user.twitch_access_token

    # Rafraîchir le token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TWITCH_TOKEN_URL,
            data={
                "client_id": settings.twitch_client_id,
                "client_secret": settings.twitch_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": user.twitch_refresh_token,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Token expiré, veuillez vous reconnecter"
            )

        token_data = response.json()
        user.twitch_access_token = token_data["access_token"]
        user.twitch_refresh_token = token_data["refresh_token"]
        user.twitch_token_expires_at = datetime.utcnow() + timedelta(
            seconds=token_data["expires_in"]
        )

        await db.commit()
        return user.twitch_access_token


@router.get("/status")
async def auth_status():
    """Vérifie si l'authentification Twitch est configurée."""
    settings = get_settings()
    return {
        "configured": bool(settings.twitch_client_id and settings.twitch_client_secret),
        "redirect_uri": settings.twitch_redirect_uri,
    }

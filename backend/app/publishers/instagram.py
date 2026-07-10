"""Publication sur Instagram (Reels)."""

import json
from pathlib import Path
from typing import Optional

from app.config import get_settings


class InstagramPublisher:
    """
    Publie des Reels sur Instagram.
    
    Utilise instagrapi (unofficial) car l'API officielle Instagram
    nécessite une review d'app pour le contenu publishing.
    """
    
    def __init__(self, session_path: Optional[Path] = None):
        """
        Args:
            session_path: Chemin vers le fichier de session
        """
        settings = get_settings()
        self.session_path = session_path or settings.data_dir / "instagram_session.json"
        self._client = None
    
    def _get_client(self):
        """Retourne le client Instagram."""
        if self._client is not None:
            return self._client
        
        from instagrapi import Client
        
        self._client = Client()
        
        # Charger la session existante
        if self.session_path.exists():
            self._client.load_settings(self.session_path)
            try:
                self._client.get_timeline_feed()
                return self._client
            except Exception:
                pass
        
        raise RuntimeError(
            "Session Instagram non configurée. "
            "Utilisez la méthode login() pour vous connecter."
        )
    
    def login(self, username: str, password: str) -> bool:
        """
        Connexion à Instagram.
        
        Args:
            username: Nom d'utilisateur Instagram
            password: Mot de passe
            
        Returns:
            True si la connexion a réussi
        """
        from instagrapi import Client
        
        self._client = Client()
        
        try:
            self._client.login(username, password)
            self._client.dump_settings(self.session_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Erreur de connexion Instagram: {e}")
    
    def upload_reel(
        self,
        video_path: Path,
        caption: str = "",
        thumbnail_path: Optional[Path] = None,
    ) -> dict:
        """
        Upload un Reel sur Instagram.
        
        Args:
            video_path: Chemin vers la vidéo (format 9:16, max 90s)
            caption: Légende du Reel
            thumbnail_path: Chemin vers la miniature (optionnel)
            
        Returns:
            Dictionnaire avec media_id et url
        """
        client = self._get_client()
        
        # Upload le Reel
        media = client.clip_upload(
            path=str(video_path),
            caption=caption,
            thumbnail=str(thumbnail_path) if thumbnail_path else None,
        )
        
        return {
            "media_id": media.id,
            "media_pk": media.pk,
            "url": f"https://www.instagram.com/reel/{media.code}/",
            "caption": caption,
        }
    
    def get_account_info(self) -> dict:
        """Récupère les informations du compte connecté."""
        client = self._get_client()
        user = client.account_info()
        
        return {
            "username": user.username,
            "full_name": user.full_name,
            "followers": user.follower_count,
            "following": user.following_count,
            "posts": user.media_count,
        }


class InstagramGraphAPI:
    """
    Publication via l'API officielle Instagram Graph.
    
    Nécessite:
    - Un compte Business ou Creator
    - Une page Facebook liée
    - Une app Facebook avec les permissions content_publish
    """
    
    def __init__(self):
        settings = get_settings()
        self.access_token = settings.instagram_access_token
        self.business_id = settings.instagram_business_id
    
    def upload_reel(
        self,
        video_url: str,
        caption: str = "",
        share_to_feed: bool = True,
    ) -> dict:
        """
        Upload un Reel via l'API Graph.
        
        Note: La vidéo doit être accessible via URL publique.
        
        Args:
            video_url: URL publique de la vidéo
            caption: Légende
            share_to_feed: Partager aussi dans le feed
            
        Returns:
            Dictionnaire avec media_id
        """
        import httpx
        
        if not self.access_token or not self.business_id:
            raise RuntimeError(
                "Instagram Graph API non configurée. "
                "Configurez INSTAGRAM_ACCESS_TOKEN et INSTAGRAM_BUSINESS_ID."
            )
        
        # Étape 1: Créer le container média
        create_url = f"https://graph.facebook.com/v18.0/{self.business_id}/media"
        
        create_response = httpx.post(
            create_url,
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": str(share_to_feed).lower(),
                "access_token": self.access_token,
            },
        )
        
        if create_response.status_code != 200:
            raise RuntimeError(f"Erreur création média: {create_response.text}")
        
        container_id = create_response.json()["id"]
        
        # Étape 2: Publier le container
        publish_url = f"https://graph.facebook.com/v18.0/{self.business_id}/media_publish"
        
        publish_response = httpx.post(
            publish_url,
            params={
                "creation_id": container_id,
                "access_token": self.access_token,
            },
        )
        
        if publish_response.status_code != 200:
            raise RuntimeError(f"Erreur publication: {publish_response.text}")
        
        media_id = publish_response.json()["id"]
        
        return {
            "media_id": media_id,
            "container_id": container_id,
        }


def upload_to_instagram(
    video_path: Path,
    caption: str = "",
    use_official_api: bool = False,
) -> dict:
    """
    Fonction utilitaire pour uploader sur Instagram.
    
    Args:
        video_path: Chemin vers la vidéo
        caption: Légende
        use_official_api: Utiliser l'API officielle (nécessite config)
        
    Returns:
        Dictionnaire avec media_id et url
    """
    if use_official_api:
        raise NotImplementedError(
            "L'API officielle nécessite une URL publique pour la vidéo. "
            "Utilisez use_official_api=False pour utiliser instagrapi."
        )
    
    publisher = InstagramPublisher()
    return publisher.upload_reel(video_path, caption)

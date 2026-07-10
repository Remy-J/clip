"""Publication sur YouTube (Shorts)."""

import pickle
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubePublisher:
    """Publie des vidéos sur YouTube."""
    
    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Args:
            credentials_path: Chemin vers le fichier credentials OAuth
        """
        settings = get_settings()
        self.credentials_path = credentials_path or settings.data_dir / "youtube_credentials.json"
        self.token_path = settings.data_dir / "youtube_token.pickle"
        self._service = None
    
    def _get_credentials(self) -> Credentials:
        """Récupère ou crée les credentials OAuth."""
        creds = None
        
        # Charger les credentials existants
        if self.token_path.exists():
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)
        
        # Rafraîchir si expiré
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    f"Fichier credentials non trouvé: {self.credentials_path}\n"
                    "Téléchargez-le depuis Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                SCOPES,
            )
            creds = flow.run_local_server(port=8080)
        
        # Sauvegarder les credentials
        with open(self.token_path, "wb") as token:
            pickle.dump(creds, token)
        
        return creds
    
    def _get_service(self):
        """Retourne le service YouTube API."""
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("youtube", "v3", credentials=creds)
        return self._service
    
    def upload_short(
        self,
        video_path: Path,
        title: str,
        description: str = "",
        tags: Optional[list[str]] = None,
        category_id: str = "22",
        privacy: str = "private",
    ) -> dict:
        """
        Upload une vidéo comme YouTube Short.
        
        Args:
            video_path: Chemin vers la vidéo
            title: Titre de la vidéo
            description: Description
            tags: Liste de tags
            category_id: ID de catégorie YouTube (22 = People & Blogs)
            privacy: Visibilité (private, unlisted, public)
            
        Returns:
            Dictionnaire avec video_id et url
        """
        service = self._get_service()
        
        # Ajouter #Shorts au titre si pas présent
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
        
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }
        
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
        )
        
        request = service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )
        
        response = request.execute()
        
        video_id = response["id"]
        
        return {
            "video_id": video_id,
            "url": f"https://youtube.com/shorts/{video_id}",
            "title": title,
            "privacy": privacy,
        }
    
    def check_quota(self) -> dict:
        """
        Vérifie l'état du quota YouTube API.
        
        Note: YouTube API ne fournit pas d'endpoint direct pour le quota.
        Cette méthode fait un appel simple pour vérifier l'authentification.
        """
        try:
            service = self._get_service()
            service.channels().list(part="snippet", mine=True).execute()
            return {"status": "ok", "authenticated": True}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def upload_to_youtube(
    video_path: Path,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    privacy: str = "private",
) -> dict:
    """
    Fonction utilitaire pour uploader sur YouTube.
    
    Args:
        video_path: Chemin vers la vidéo
        title: Titre
        description: Description
        tags: Tags
        privacy: Visibilité
        
    Returns:
        Dictionnaire avec video_id et url
    """
    publisher = YouTubePublisher()
    return publisher.upload_short(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy=privacy,
    )

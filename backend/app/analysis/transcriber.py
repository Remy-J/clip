"""Transcription audio avec Whisper local (faster-whisper)."""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class TranscriptSegment:
    """Segment de transcription avec timestamps."""
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    """Transcription complète avec tous les segments."""
    segments: list[TranscriptSegment]
    language: str
    duration: float

    def get_text_between(self, start: float, end: float) -> str:
        """Retourne le texte entre deux timestamps."""
        return " ".join(
            seg.text for seg in self.segments
            if seg.start >= start and seg.end <= end
        )

    def to_dict(self) -> dict:
        """Convertit en dictionnaire."""
        return {
            "language": self.language,
            "duration": self.duration,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in self.segments
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        """Crée une instance depuis un dictionnaire."""
        return cls(
            language=data["language"],
            duration=data["duration"],
            segments=[
                TranscriptSegment(**seg) for seg in data["segments"]
            ],
        )

    def save(self, path: Path) -> None:
        """Sauvegarde la transcription en JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Transcript":
        """Charge une transcription depuis un fichier JSON."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class Transcriber:
    """Transcripteur utilisant faster-whisper."""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialise le transcripteur.

        Args:
            model_name: Nom du modèle Whisper (tiny, base, small, medium, large-v3)
            device: Device à utiliser (auto, cpu, cuda)
        """
        settings = get_settings()
        self.model_name = model_name or settings.whisper_model
        self.device = device or settings.whisper_device
        self._model = None

    def _load_model(self):
        """Charge le modèle Whisper."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        compute_type = "float16" if self.device == "cuda" else "int8"

        if self.device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        else:
            device = self.device

        self._model = WhisperModel(
            self.model_name,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
    ) -> Transcript:
        """
        Transcrit un fichier audio.

        Args:
            audio_path: Chemin vers le fichier audio/vidéo
            language: Code langue (ex: 'fr', 'en'). Auto-détecté si non spécifié.

        Returns:
            Transcript avec tous les segments
        """
        self._load_model()

        segments_iter, info = self._model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=False,
            vad_filter=True,
        )

        segments = []
        for segment in segments_iter:
            segments.append(TranscriptSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
            ))

        return Transcript(
            segments=segments,
            language=info.language,
            duration=info.duration,
        )


def transcribe_video(
    video_path: Path,
    output_path: Optional[Path] = None,
    language: Optional[str] = None,
) -> Transcript:
    """
    Fonction utilitaire pour transcrire une vidéo.

    Args:
        video_path: Chemin vers le fichier vidéo
        output_path: Chemin de sauvegarde (optionnel)
        language: Code langue (optionnel)

    Returns:
        Transcript
    """
    transcriber = Transcriber()
    transcript = transcriber.transcribe(video_path, language)

    if output_path:
        transcript.save(output_path)

    return transcript

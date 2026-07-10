"""Analyse LLM avec Ollama pour détecter les moments intéressants."""

from dataclasses import dataclass
from typing import Optional

import ollama

from app.config import get_settings


@dataclass
class HighlightAnalysis:
    """Résultat de l'analyse LLM d'un segment."""
    category: str
    score: float
    reason: str
    suggested_title: Optional[str] = None


ANALYSIS_PROMPT = """Tu es un expert en création de contenu viral pour YouTube Shorts et Instagram Reels.

Analyse le texte suivant extrait d'un stream Twitch et détermine s'il contient un moment intéressant pour créer un clip viral.

TEXTE À ANALYSER:
{text}

CONTEXTE (si disponible):
- Timestamp: {start_time} - {end_time}
- Durée: {duration} secondes

Réponds UNIQUEMENT avec un JSON valide (sans commentaires, sans texte avant ou après):
{{
    "is_highlight": true ou false,
    "category": "drole" | "instructif" | "marquant" | "dynamique" | "aucun",
    "score": nombre entre 0 et 10,
    "reason": "explication courte",
    "suggested_title": "titre accrocheur pour le clip (si is_highlight=true)"
}}

Critères d'évaluation:
- DROLE: Blagues, situations comiques, réactions amusantes, fails drôles
- INSTRUCTIF: Conseils utiles, astuces, explications claires, moments éducatifs
- MARQUANT: Moments émotionnels, victoires/défaites importantes, révélations
- DYNAMIQUE: Action intense, gameplay impressionnant, moments de tension

Score:
- 0-3: Pas intéressant, contenu banal
- 4-6: Potentiellement intéressant, pourrait fonctionner
- 7-10: Très intéressant, fort potentiel viral

Sois strict dans ton évaluation. Seuls les moments vraiment intéressants méritent un score > 6.
"""


class LLMAnalyzer:
    """Analyseur utilisant un LLM local via Ollama."""

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None):
        """
        Args:
            model: Nom du modèle Ollama (ex: llama3.1:8b)
            host: URL du serveur Ollama
        """
        settings = get_settings()
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self._client = None

    def _get_client(self):
        """Retourne le client Ollama."""
        if self._client is None:
            self._client = ollama.Client(host=self.host)
        return self._client

    def analyze_segment(
        self,
        text: str,
        start_time: float,
        end_time: float,
    ) -> HighlightAnalysis:
        """
        Analyse un segment de transcription.

        Args:
            text: Texte du segment
            start_time: Timestamp de début
            end_time: Timestamp de fin

        Returns:
            HighlightAnalysis avec le résultat
        """
        import json

        duration = end_time - start_time

        prompt = ANALYSIS_PROMPT.format(
            text=text,
            start_time=f"{int(start_time // 60)}:{int(start_time % 60):02d}",
            end_time=f"{int(end_time // 60)}:{int(end_time % 60):02d}",
            duration=f"{duration:.1f}",
        )

        client = self._get_client()

        response = client.generate(
            model=self.model,
            prompt=prompt,
            options={
                "temperature": 0.3,
                "num_predict": 500,
            },
        )

        response_text = response["response"].strip()

        # Parser le JSON de la réponse
        try:
            # Extraire le JSON de la réponse
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("Pas de JSON trouvé dans la réponse")

            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            if not data.get("is_highlight", False):
                return HighlightAnalysis(
                    category="aucun",
                    score=0.0,
                    reason=data.get("reason", "Pas de moment intéressant"),
                )

            return HighlightAnalysis(
                category=data.get("category", "aucun"),
                score=float(data.get("score", 0)),
                reason=data.get("reason", ""),
                suggested_title=data.get("suggested_title"),
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            return HighlightAnalysis(
                category="erreur",
                score=0.0,
                reason=f"Erreur de parsing: {str(e)}",
            )

    def analyze_transcript_segments(
        self,
        transcript,
        window_size: float = 30.0,
        overlap: float = 10.0,
        min_score: float = 5.0,
    ) -> list[tuple[float, float, HighlightAnalysis]]:
        """
        Analyse une transcription complète par fenêtres glissantes.

        Args:
            transcript: Transcript avec segments
            window_size: Taille de la fenêtre en secondes
            overlap: Chevauchement entre fenêtres
            min_score: Score minimum pour garder un highlight

        Returns:
            Liste de (start, end, analysis)
        """
        results = []
        current_time = 0.0

        while current_time < transcript.duration:
            end_time = min(current_time + window_size, transcript.duration)

            text = transcript.get_text_between(current_time, end_time)

            if text.strip():
                analysis = self.analyze_segment(text, current_time, end_time)

                if analysis.score >= min_score:
                    results.append((current_time, end_time, analysis))

            current_time += window_size - overlap

        return results


def check_ollama_available() -> tuple[bool, str]:
    """
    Vérifie si Ollama est disponible et le modèle est installé.

    Returns:
        (disponible, message)
    """
    settings = get_settings()

    try:
        client = ollama.Client(host=settings.ollama_host)
        models = client.list()

        model_names = [m["name"] for m in models.get("models", [])]

        if settings.ollama_model in model_names or any(
            settings.ollama_model.split(":")[0] in m for m in model_names
        ):
            return True, f"Ollama OK, modèle {settings.ollama_model} disponible"

        return False, (
            f"Modèle {settings.ollama_model} non trouvé. "
            f"Installez-le avec: ollama pull {settings.ollama_model}"
        )

    except Exception as e:
        return False, f"Ollama non disponible: {str(e)}. Lancez 'ollama serve'."

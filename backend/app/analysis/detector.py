"""Détecteur de highlights combinant audio et LLM."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.analysis.transcriber import Transcript, transcribe_video
from app.analysis.audio import AudioAnalysis, analyze_video_audio, AudioAnalyzer
from app.analysis.llm import LLMAnalyzer, HighlightAnalysis


@dataclass
class DetectedHighlight:
    """Highlight détecté avec toutes les métadonnées."""
    start_time: float
    end_time: float
    duration: float
    
    # Scores
    audio_score: float
    llm_score: float
    combined_score: float
    
    # Analyse LLM
    category: str
    reason: str
    suggested_title: Optional[str]
    
    # Texte
    transcript_excerpt: str


class HighlightDetector:
    """
    Détecteur de highlights combinant analyse audio et LLM.
    
    Pipeline:
    1. Transcrire la vidéo avec Whisper
    2. Analyser l'audio pour détecter les pics d'énergie
    3. Pour chaque segment potentiel, analyser avec le LLM
    4. Combiner les scores et retourner les meilleurs highlights
    """

    def __init__(
        self,
        min_duration: float = 15.0,
        max_duration: float = 60.0,
        min_combined_score: float = 0.5,
        audio_weight: float = 0.3,
        llm_weight: float = 0.7,
    ):
        """
        Args:
            min_duration: Durée minimale d'un highlight en secondes
            max_duration: Durée maximale d'un highlight en secondes
            min_combined_score: Score combiné minimum (0-1)
            audio_weight: Poids de l'analyse audio dans le score combiné
            llm_weight: Poids de l'analyse LLM dans le score combiné
        """
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_combined_score = min_combined_score
        self.audio_weight = audio_weight
        self.llm_weight = llm_weight

    async def detect(
        self,
        video_path: Path,
        transcript: Optional[Transcript] = None,
        max_highlights: int = 10,
        progress_callback=None,
    ) -> list[DetectedHighlight]:
        """
        Détecte les highlights dans une vidéo.
        
        Args:
            video_path: Chemin vers la vidéo
            transcript: Transcription pré-calculée (optionnel)
            max_highlights: Nombre maximum de highlights à retourner
            progress_callback: Callback de progression (0-100)
            
        Returns:
            Liste de DetectedHighlight triés par score
        """
        highlights = []
        
        # Étape 1: Transcription (si nécessaire)
        if progress_callback:
            progress_callback(0)
            
        if transcript is None:
            transcript = transcribe_video(video_path)
            
        if progress_callback:
            progress_callback(30)
        
        # Étape 2: Analyse audio
        audio_analysis = analyze_video_audio(video_path)
        audio_analyzer = AudioAnalyzer()
        audio_segments = audio_analyzer.find_highlight_segments(
            audio_analysis,
            min_duration=self.min_duration,
            max_duration=self.max_duration,
        )
        
        if progress_callback:
            progress_callback(50)
        
        # Étape 3: Analyse LLM des segments audio
        llm_analyzer = LLMAnalyzer()
        
        total_segments = len(audio_segments)
        
        for i, (start, end, audio_score) in enumerate(audio_segments):
            # Extraire le texte du segment
            text = transcript.get_text_between(start, end)
            
            if not text.strip():
                continue
            
            # Analyser avec le LLM
            llm_result = llm_analyzer.analyze_segment(text, start, end)
            
            # Normaliser les scores (audio: écarts-types -> 0-1, LLM: 0-10 -> 0-1)
            normalized_audio = min(1.0, max(0.0, audio_score / 3.0))
            normalized_llm = llm_result.score / 10.0
            
            # Score combiné
            combined_score = (
                self.audio_weight * normalized_audio +
                self.llm_weight * normalized_llm
            )
            
            if combined_score >= self.min_combined_score:
                highlights.append(DetectedHighlight(
                    start_time=start,
                    end_time=end,
                    duration=end - start,
                    audio_score=audio_score,
                    llm_score=llm_result.score,
                    combined_score=combined_score,
                    category=llm_result.category,
                    reason=llm_result.reason,
                    suggested_title=llm_result.suggested_title,
                    transcript_excerpt=text[:500],
                ))
            
            if progress_callback:
                progress = 50 + int((i + 1) / total_segments * 40)
                progress_callback(progress)
        
        # Étape 4: Analyse LLM des segments supplémentaires (fenêtre glissante)
        # Pour ne pas rater des moments qui n'ont pas de pic audio
        llm_segments = llm_analyzer.analyze_transcript_segments(
            transcript,
            window_size=30.0,
            overlap=15.0,
            min_score=7.0,
        )
        
        for start, end, llm_result in llm_segments:
            # Vérifier qu'on n'a pas déjà ce segment
            if any(
                abs(h.start_time - start) < 10 and abs(h.end_time - end) < 10
                for h in highlights
            ):
                continue
            
            # Chercher le score audio correspondant
            audio_score = 0.0
            for seg in audio_analysis.segments:
                if seg.start >= start and seg.end <= end:
                    audio_score = max(audio_score, seg.energy_score)
            
            normalized_audio = min(1.0, max(0.0, audio_score / 3.0))
            normalized_llm = llm_result.score / 10.0
            
            combined_score = (
                self.audio_weight * normalized_audio +
                self.llm_weight * normalized_llm
            )
            
            if combined_score >= self.min_combined_score:
                text = transcript.get_text_between(start, end)
                
                highlights.append(DetectedHighlight(
                    start_time=start,
                    end_time=min(end, start + self.max_duration),
                    duration=min(end - start, self.max_duration),
                    audio_score=audio_score,
                    llm_score=llm_result.score,
                    combined_score=combined_score,
                    category=llm_result.category,
                    reason=llm_result.reason,
                    suggested_title=llm_result.suggested_title,
                    transcript_excerpt=text[:500],
                ))
        
        if progress_callback:
            progress_callback(100)
        
        # Trier par score et limiter
        highlights.sort(key=lambda h: h.combined_score, reverse=True)
        return highlights[:max_highlights]


async def detect_highlights(
    video_path: Path,
    max_highlights: int = 10,
    min_score: float = 0.5,
) -> list[DetectedHighlight]:
    """
    Fonction utilitaire pour détecter les highlights.
    
    Args:
        video_path: Chemin vers la vidéo
        max_highlights: Nombre maximum de highlights
        min_score: Score minimum (0-1)
        
    Returns:
        Liste de DetectedHighlight
    """
    detector = HighlightDetector(min_combined_score=min_score)
    return await detector.detect(video_path, max_highlights=max_highlights)

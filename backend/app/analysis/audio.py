"""Analyse audio avec Librosa pour détecter les moments intéressants."""

import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class AudioSegment:
    """Segment audio avec score d'intensité."""
    start: float
    end: float
    energy_score: float
    is_peak: bool


@dataclass
class AudioAnalysis:
    """Résultat de l'analyse audio."""
    segments: list[AudioSegment]
    peaks: list[AudioSegment]
    duration: float
    average_energy: float


def extract_audio(video_path: Path, output_path: Path, sample_rate: int = 22050) -> Path:
    """
    Extrait l'audio d'une vidéo avec FFmpeg.

    Args:
        video_path: Chemin vers la vidéo
        output_path: Chemin de sortie pour l'audio
        sample_rate: Taux d'échantillonnage

    Returns:
        Chemin du fichier audio extrait
    """
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        "-y",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erreur FFmpeg: {result.stderr}")

    return output_path


class AudioAnalyzer:
    """Analyseur audio pour détecter les moments d'intensité."""

    def __init__(
        self,
        window_size: float = 2.0,
        hop_size: float = 0.5,
        peak_threshold: float = 1.5,
    ):
        """
        Args:
            window_size: Taille de la fenêtre d'analyse en secondes
            hop_size: Pas entre les fenêtres en secondes
            peak_threshold: Seuil de détection des pics (en écarts-types)
        """
        self.window_size = window_size
        self.hop_size = hop_size
        self.peak_threshold = peak_threshold

    def analyze(self, audio_path: Path) -> AudioAnalysis:
        """
        Analyse un fichier audio et détecte les moments intéressants.

        Args:
            audio_path: Chemin vers le fichier audio

        Returns:
            AudioAnalysis avec les segments et pics détectés
        """
        import librosa

        # Charger l'audio
        y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
        duration = len(y) / sr

        # Calculer l'énergie RMS par fenêtre
        window_samples = int(self.window_size * sr)
        hop_samples = int(self.hop_size * sr)

        # Utiliser librosa pour calculer le RMS
        rms = librosa.feature.rms(
            y=y,
            frame_length=window_samples,
            hop_length=hop_samples,
        )[0]

        # Timestamps pour chaque fenêtre
        times = librosa.frames_to_time(
            np.arange(len(rms)),
            sr=sr,
            hop_length=hop_samples,
        )

        # Normaliser les énergies
        mean_energy = np.mean(rms)
        std_energy = np.std(rms)

        segments = []
        peaks = []

        for i, (time, energy) in enumerate(zip(times, rms)):
            # Score normalisé (nombre d'écarts-types au-dessus de la moyenne)
            if std_energy > 0:
                score = (energy - mean_energy) / std_energy
            else:
                score = 0.0

            is_peak = score >= self.peak_threshold

            segment = AudioSegment(
                start=float(time),
                end=float(min(time + self.window_size, duration)),
                energy_score=float(score),
                is_peak=is_peak,
            )

            segments.append(segment)
            if is_peak:
                peaks.append(segment)

        return AudioAnalysis(
            segments=segments,
            peaks=peaks,
            duration=duration,
            average_energy=float(mean_energy),
        )

    def find_highlight_segments(
        self,
        analysis: AudioAnalysis,
        min_duration: float = 10.0,
        max_duration: float = 60.0,
        merge_gap: float = 5.0,
    ) -> list[tuple[float, float, float]]:
        """
        Trouve des segments highlight en fusionnant les pics proches.

        Args:
            analysis: Résultat de l'analyse audio
            min_duration: Durée minimale d'un highlight
            max_duration: Durée maximale d'un highlight
            merge_gap: Écart maximum pour fusionner deux pics

        Returns:
            Liste de tuples (start, end, score)
        """
        if not analysis.peaks:
            return []

        # Trier les pics par timestamp
        sorted_peaks = sorted(analysis.peaks, key=lambda x: x.start)

        # Fusionner les pics proches
        merged_segments = []
        current_start = sorted_peaks[0].start
        current_end = sorted_peaks[0].end
        current_scores = [sorted_peaks[0].energy_score]

        for peak in sorted_peaks[1:]:
            if peak.start - current_end <= merge_gap:
                current_end = peak.end
                current_scores.append(peak.energy_score)
            else:
                avg_score = sum(current_scores) / len(current_scores)
                merged_segments.append((current_start, current_end, avg_score))
                current_start = peak.start
                current_end = peak.end
                current_scores = [peak.energy_score]

        # Ajouter le dernier segment
        avg_score = sum(current_scores) / len(current_scores)
        merged_segments.append((current_start, current_end, avg_score))

        # Étendre les segments pour atteindre la durée minimale
        extended_segments = []
        for start, end, score in merged_segments:
            duration = end - start
            if duration < min_duration:
                extension = (min_duration - duration) / 2
                start = max(0, start - extension)
                end = min(analysis.duration, end + extension)

            if end - start > max_duration:
                end = start + max_duration

            extended_segments.append((start, end, score))

        return extended_segments


def analyze_video_audio(
    video_path: Path,
    temp_dir: Optional[Path] = None,
) -> AudioAnalysis:
    """
    Analyse l'audio d'une vidéo.

    Args:
        video_path: Chemin vers la vidéo
        temp_dir: Répertoire temporaire pour l'audio extrait

    Returns:
        AudioAnalysis
    """
    import tempfile

    if temp_dir is None:
        temp_dir = Path(tempfile.gettempdir())

    audio_path = temp_dir / f"{video_path.stem}_audio.wav"

    try:
        extract_audio(video_path, audio_path)
        analyzer = AudioAnalyzer()
        return analyzer.analyze(audio_path)
    finally:
        if audio_path.exists():
            audio_path.unlink()

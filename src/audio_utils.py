"""
Audio file utilities for the pronunciation assessment system.

This module provides helper functions for:
- Loading and validating audio files
- Managing audio file paths and metadata
- Batch processing audio files
"""

from pathlib import Path
from typing import List, Optional
import soundfile as sf


def validate_audio_file(audio_path: Path | str) -> bool:
    """
    Check if audio file exists and is readable.

    Args:
        audio_path: Path to audio file

    Returns:
        True if file exists and is a valid audio file

    Examples:
        >>> validate_audio_file("data/sample_audio/ni_hao.wav")
        True
        >>> validate_audio_file("nonexistent.wav")
        False
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        return False

    if not audio_path.is_file():
        return False

    # Check if it's a WAV file (or other supported format)
    if audio_path.suffix.lower() not in ['.wav', '.mp3', '.flac', '.ogg', '.m4a']:
        return False

    return True


def get_audio_duration(audio_path: Path | str) -> Optional[float]:
    """
    Get duration of audio file in seconds.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds, or None if file cannot be read

    Examples:
        >>> get_audio_duration("data/sample_audio/ni_hao.wav")
        3.0
    """
    try:
        audio_path = Path(audio_path)
        info = sf.info(str(audio_path))
        return info.duration
    except Exception:
        return None


def get_audio_files(directory: Path | str, pattern: str = "*.wav") -> List[Path]:
    """
    Get list of audio files in directory matching pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern (default: "*.wav")

    Returns:
        Sorted list of audio file paths

    Examples:
        >>> files = get_audio_files("data/sample_audio")
        >>> len(files)
        10
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    return sorted(directory.glob(pattern))


def ensure_directory_exists(directory: Path | str) -> Path:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        directory: Directory path

    Returns:
        Path object for the directory

    Examples:
        >>> ensure_directory_exists("results")
        PosixPath('results')
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_filename_without_extension(file_path: Path | str) -> str:
    """
    Get filename without extension.

    Args:
        file_path: File path

    Returns:
        Filename without extension

    Examples:
        >>> get_filename_without_extension("data/audio/eval_ni_hao_perfect_001.wav")
        'eval_ni_hao_perfect_001'
    """
    return Path(file_path).stem


def construct_audio_path(base_dir: Path | str, filename: str, extension: str = ".wav") -> Path:
    """
    Construct full audio file path from components.

    Args:
        base_dir: Base directory
        filename: Filename (with or without extension)
        extension: File extension (default: ".wav")

    Returns:
        Full path to audio file

    Examples:
        >>> construct_audio_path("data/eval_audio", "eval_ni_hao_perfect_001")
        PosixPath('data/eval_audio/eval_ni_hao_perfect_001.wav')
    """
    base_dir = Path(base_dir)
    filename = Path(filename).stem  # Remove extension if present

    if not extension.startswith('.'):
        extension = '.' + extension

    return base_dir / (filename + extension)

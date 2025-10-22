"""
Audio file utilities for the pronunciation assessment system.

This module provides helper functions for:
- Loading and validating audio files
- Managing audio file paths and metadata
- Batch processing audio files
"""

from pathlib import Path
from typing import List, Optional, Union
import soundfile as sf
import sounddevice as sd
import yaml


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


def record_audio(
    duration: int = 3,
    filename: Optional[str] = None,
    output_dir: Path | str = Path("data/eval_audio"),
    sample_rate: int = 16000,
    channels: int = 1
) -> tuple:
    """
    Record audio from microphone.

    Args:
        duration: Recording duration in seconds (default: 3)
        filename: Optional filename to save (without extension)
        output_dir: Directory to save recordings (default: "data/eval_audio")
        sample_rate: Sample rate in Hz (default: 16000)
        channels: Number of channels (default: 1 for mono)

    Returns:
        Tuple of (audio_data, sample_rate)

    Examples:
        >>> audio_data, sr = record_audio(duration=3, filename="test_recording")
        Recording for 3 seconds...
        Start speaking now!
        Recording complete!
        Saved to: data/eval_audio/test_recording.wav
    """
    print(f"Recording for {duration} seconds...")
    print("Start speaking now!")

    # Record audio
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype='float32'
    )
    sd.wait()  # Wait until recording is finished

    print("Recording complete!")

    # Save if filename provided
    if filename:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{filename}.wav"
        sf.write(filepath, audio_data, sample_rate)
        print(f"Saved to: {filepath}")

    return audio_data, sample_rate


def play_audio(
    audio_path: Union[Path, str, List[Union[Path, str]]],
    base_dir: Optional[Path | str] = None,
    wait: bool = True
) -> None:
    """
    Play audio file(s) through system speakers.

    Args:
        audio_path: Path to audio file, or list of paths, or filename(s)
        base_dir: Base directory if audio_path is just a filename (default: None)
        wait: Whether to wait for playback to finish before returning (default: True)

    Examples:
        >>> # Play single file
        >>> play_audio("data/eval_audio/eval_ni_hao_perfect_001.wav")

        >>> # Play from filename with base_dir
        >>> play_audio("eval_ni_hao_perfect_001", base_dir="data/eval_audio")

        >>> # Play multiple files
        >>> play_audio(["eval_ni_hao_perfect_001", "eval_xie_xie_perfect_001"],
        ...            base_dir="data/eval_audio")
    """
    # Handle single path vs list of paths
    if isinstance(audio_path, (list, tuple)):
        for path in audio_path:
            play_audio(path, base_dir=base_dir, wait=wait)
        return

    # Construct full path if needed
    if base_dir is not None:
        audio_path = construct_audio_path(base_dir, str(audio_path))
    else:
        audio_path = Path(audio_path)

    # Check if file exists
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return

    # Load and play audio
    try:
        audio_data, sample_rate = sf.read(str(audio_path))
        print(f"Playing: {audio_path.name}")
        sd.play(audio_data, sample_rate)

        if wait:
            sd.wait()  # Wait until playback is finished
            print(f"Finished playing: {audio_path.name}")

    except Exception as e:
        print(f"Error playing audio: {e}")


def record_phrase_batch(
    yaml_path: Path | str,
    output_dir: Path | str = Path("data/eval_audio"),
    default_duration: int = 3,
    sample_rate: int = 16000
) -> None:
    """
    Record multiple phrases with prompts from YAML metadata file.

    This function helps batch-record test cases by reading metadata from YAML
    and prompting the user to record each phrase with appropriate instructions.

    Args:
        yaml_path: Path to YAML file with test cases
        output_dir: Directory to save recordings (default: "data/eval_audio")
        default_duration: Default recording duration in seconds (default: 3)
        sample_rate: Sample rate in Hz (default: 16000)

    Examples:
        >>> record_phrase_batch("data/eval_metadata.yml")
        Recording session starting!
        Total phrases to record: 50
        Press Enter to begin...
    """
    # Load test cases from YAML
    yaml_path = Path(yaml_path)
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    test_cases = data['test_cases']

    print(f"Recording session starting!")
    print(f"Total phrases to record: {len(test_cases)}\n")
    input("Press Enter to begin...")

    for i, case in enumerate(test_cases, 1):
        filename = case['filename']
        expected = case['expected_chinese']
        expected_pinyin = case['expected_pinyin']
        target_pronunciation = case.get('pronunciation_target', expected_pinyin)
        error_type = case['error_type']
        target_error = case.get('target_error', 'Correct pronunciation')
        duration = case.get('duration', default_duration)

        print(f"\n{'='*60}")
        print(f"Recording {i}/{len(test_cases)}: {filename}")
        print(f"{'='*60}")
        print(f"Chinese:  {expected}")
        print(f"Expected: {expected_pinyin}")

        if error_type == 'correct':
            print(f"💚 Pronounce CORRECTLY: {target_pronunciation}")
        else:
            print(f"❌ Pronounce INCORRECTLY: {target_pronunciation}")
            print(f"   ({target_error})")

        print(f"Duration: {duration}s")
        input("\nPress Enter when ready to record...")

        # Record
        record_audio(
            duration=duration,
            filename=filename,
            output_dir=output_dir,
            sample_rate=sample_rate
        )
        print("✓ Recorded\n")

    print("\n" + "="*60)
    print("All recordings complete!")
    print(f"Files saved to: {output_dir}")

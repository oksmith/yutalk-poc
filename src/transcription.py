"""
Transcription utilities for converting audio to Chinese text and pinyin.

This module provides functions for:
- Transcribing audio using OpenAI Whisper API
- Converting Chinese text to pinyin
- Traditional to simplified Chinese conversion
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI
from pypinyin import pinyin, Style
from opencc import OpenCC


def get_openai_client() -> OpenAI:
    """
    Get initialized OpenAI client.

    Returns:
        OpenAI client instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def transcribe_whisper(
    audio_path: Path | str,
    language: str = "zh",
    client: Optional[OpenAI] = None
) -> Dict:
    """
    Transcribe audio using OpenAI Whisper.

    Args:
        audio_path: Path to audio file
        language: Language code (zh for Mandarin)
        client: Optional pre-initialized OpenAI client

    Returns:
        dict with transcription and metadata:
            - text: Transcribed text (may be Chinese characters or romanization)
            - language: Detected/specified language
            - duration: Audio duration in seconds
            - segments: Timestamped segments (if available)
    """
    if client is None:
        client = get_openai_client()

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="verbose_json"
        )

    # Convert segments to JSON-serializable format if present
    segments = None
    if hasattr(response, 'segments') and response.segments:
        segments = [
            {
                'id': seg.id,
                'start': seg.start,
                'end': seg.end,
                'text': seg.text
            }
            for seg in response.segments
        ]

    return {
        'text': response.text,
        'language': response.language,
        'duration': response.duration,
        'segments': segments
    }


def text_to_pinyin(text: str, style: Style = Style.TONE3) -> List[str]:
    """
    Convert Chinese text to pinyin.

    Args:
        text: Chinese characters
        style: Pinyin style (TONE3 = numeric tones like 'ni3 hao3')

    Returns:
        List of pinyin syllables

    Examples:
        >>> text_to_pinyin("你好")
        ['ni3', 'hao3']
        >>> text_to_pinyin("妈妈")
        ['ma1', 'ma1']
    """
    result = pinyin(text, style=style, heteronym=False)
    # Flatten the nested list
    return [syllable[0] for syllable in result]


def text_to_pinyin_display(text: str) -> str:
    """
    Get pinyin with tone marks for display.

    Args:
        text: Chinese characters

    Returns:
        Pinyin string with tone marks (e.g., "nǐ hǎo")

    Examples:
        >>> text_to_pinyin_display("你好")
        'nǐ hǎo'
    """
    result = pinyin(text, style=Style.TONE)
    return ' '.join([syllable[0] for syllable in result])


def convert_traditional_to_simplified(text: str) -> str:
    """
    Convert traditional Chinese characters to simplified.

    Whisper sometimes returns traditional characters, so we normalize to simplified.

    Args:
        text: Chinese text (may contain traditional characters)

    Returns:
        Text with all characters converted to simplified
    """
    cc = OpenCC('t2s')  # t2s = traditional to simplified
    return cc.convert(text)


def is_romanization(text: str) -> bool:
    """
    Check if transcription result is romanized (not Chinese characters).

    This happens when Whisper can't confidently match audio to Chinese phonemes.
    Common with very poor pronunciation from beginners.

    Args:
        text: Transcription result from Whisper

    Returns:
        True if text appears to be romanization rather than Chinese characters

    Examples:
        >>> is_romanization("你好")
        False
        >>> is_romanization("Ni Hao")
        True
        >>> is_romanization("ni hao")
        True
    """
    # If text contains any Chinese characters, it's not romanization
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs range
            return False

    # If no Chinese characters found, likely romanization
    # (but could also be empty or punctuation only)
    return len(text.strip()) > 0


def calculate_api_cost(duration_seconds: float) -> float:
    """
    Calculate OpenAI Whisper API cost.

    Pricing: $0.006 per minute

    Args:
        duration_seconds: Total audio duration in seconds

    Returns:
        Estimated cost in USD
    """
    minutes = duration_seconds / 60
    return minutes * 0.006

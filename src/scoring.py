"""
Pronunciation scoring and assessment functions.

This module provides phoneme-level analysis of Mandarin pronunciation by:
- Decomposing pinyin into initial, final, and tone components
- Comparing expected vs actual pronunciation
- Generating detailed feedback and scores
"""

from dataclasses import dataclass
from typing import Dict, List
from .transcription import text_to_pinyin
from pypinyin import Style


@dataclass
class Syllable:
    """
    Represents a Mandarin syllable with phonetic components.

    Mandarin syllable structure: (Initial) + Final + Tone
    - Initial: Optional consonant at start (b, p, m, f, d, t, n, l, etc.)
    - Final: Vowel + optional nasal ending (a, o, e, i, u, ü, an, en, ang, eng, etc.)
    - Tone: 1 (flat), 2 (rising), 3 (fall-rise), 4 (falling), 5 (neutral)

    Attributes:
        full: Full pinyin syllable (e.g., 'ni3')
        initial: Initial consonant (e.g., 'n')
        final: Final vowel/ending (e.g., 'i')
        tone: Tone number (e.g., '3')
    """
    full: str
    initial: str
    final: str
    tone: str


# Mandarin initial consonants
INITIALS = [
    'b', 'p', 'm', 'f',      # Labials
    'd', 't', 'n', 'l',      # Alveolars
    'g', 'k', 'h',           # Velars
    'j', 'q', 'x',           # Palatals
    'zh', 'ch', 'sh', 'r',   # Retroflexes (check these first - longer)
    'z', 'c', 's',           # Dentals
    'y', 'w'                 # Semivowels
]

# Sort by length (longest first) to check 'zh', 'ch', 'sh' before 'z', 'c', 's'
INITIALS_SORTED = sorted(INITIALS, key=len, reverse=True)

# Tone names for human-readable feedback
TONE_NAMES = {
    '1': 'first tone (flat)',
    '2': 'second tone (rising)',
    '3': 'third tone (fall-rise)',
    '4': 'fourth tone (falling)',
    '5': 'neutral tone'
}


def decompose_pinyin(pinyin_syllable: str) -> Syllable:
    """
    Break pinyin into initial, final, and tone components.

    Args:
        pinyin_syllable: Pinyin with numeric tone (e.g., 'ni3', 'hao3', 'zhi1')

    Returns:
        Syllable object with components separated

    Examples:
        >>> decompose_pinyin('ni3')
        Syllable(full='ni3', initial='n', final='i', tone='3')
        >>> decompose_pinyin('hao3')
        Syllable(full='hao3', initial='h', final='ao', tone='3')
        >>> decompose_pinyin('zhi1')
        Syllable(full='zhi1', initial='zh', final='i', tone='1')
    """
    # Extract tone (last character if it's a digit)
    if pinyin_syllable and pinyin_syllable[-1].isdigit():
        tone = pinyin_syllable[-1]
        base = pinyin_syllable[:-1]
    else:
        tone = '5'  # Neutral tone
        base = pinyin_syllable

    # Find initial (longest matching prefix)
    initial = ''
    final = base

    for init in INITIALS_SORTED:
        if base.startswith(init):
            initial = init
            final = base[len(init):]
            break

    return Syllable(
        full=pinyin_syllable,
        initial=initial,
        final=final,
        tone=tone
    )


def compare_syllables(expected: Syllable, actual: Syllable) -> Dict:
    """
    Compare two syllables and identify differences.

    Args:
        expected: What should have been pronounced
        actual: What was actually pronounced

    Returns:
        Dictionary containing:
            - match: bool (True if exact match)
            - initial_match: bool
            - final_match: bool
            - tone_match: bool
            - feedback: str (human-readable description of error)

    Examples:
        >>> exp = decompose_pinyin('ma1')
        >>> act = decompose_pinyin('ma1')
        >>> compare_syllables(exp, act)['match']
        True

        >>> exp = decompose_pinyin('ni3')
        >>> act = decompose_pinyin('li3')
        >>> result = compare_syllables(exp, act)
        >>> result['initial_match']
        False
        >>> result['tone_match']
        True
    """
    if expected.full == actual.full:
        return {
            'match': True,
            'initial_match': True,
            'final_match': True,
            'tone_match': True,
            'feedback': ' Correct'
        }

    initial_match = expected.initial == actual.initial
    final_match = expected.final == actual.final
    tone_match = expected.tone == actual.tone

    # Generate specific feedback
    errors = []
    if not initial_match:
        errors.append(f"initial: '{expected.initial}' � '{actual.initial}'")
    if not final_match:
        errors.append(f"final: '{expected.final}' � '{actual.final}'")
    if not tone_match:
        errors.append(
            f"tone: {TONE_NAMES.get(expected.tone, expected.tone)} � "
            f"{TONE_NAMES.get(actual.tone, actual.tone)}"
        )

    feedback = " " + ", ".join(errors)

    return {
        'match': False,
        'initial_match': initial_match,
        'final_match': final_match,
        'tone_match': tone_match,
        'feedback': feedback
    }


def generate_feedback_summary(comparisons: List[Dict]) -> str:
    """
    Generate human-readable feedback summary from syllable comparisons.

    Args:
        comparisons: List of comparison results from compare_syllables()

    Returns:
        Summary string describing all errors found

    Examples:
        >>> # Perfect pronunciation
        >>> generate_feedback_summary([{'match': True}])
        ' Perfect pronunciation!'

        >>> # Some errors
        >>> generate_feedback_summary([
        ...     {'match': False, 'tone_match': False, 'initial_match': True, 'final_match': True},
        ...     {'match': True, 'tone_match': True, 'initial_match': True, 'final_match': True}
        ... ])
        'Issues: 1 tone error(s)'
    """
    if all(c['match'] for c in comparisons):
        return " Perfect pronunciation!"

    tone_errors = sum(1 for c in comparisons if not c['tone_match'])
    initial_errors = sum(1 for c in comparisons if not c['initial_match'])
    final_errors = sum(1 for c in comparisons if not c['final_match'])

    feedback_parts = []
    if tone_errors > 0:
        feedback_parts.append(f"{tone_errors} tone error(s)")
    if initial_errors > 0:
        feedback_parts.append(f"{initial_errors} initial consonant error(s)")
    if final_errors > 0:
        feedback_parts.append(f"{final_errors} vowel/final error(s)")

    return "Issues: " + ", ".join(feedback_parts)


def assess_pronunciation(expected_chinese: str, actual_chinese: str) -> Dict:
    """
    Complete pronunciation assessment comparing expected vs actual Chinese text.

    This is the main entry point for pronunciation scoring. It:
    1. Converts both texts to pinyin
    2. Decomposes into phonetic components
    3. Compares syllable-by-syllable
    4. Calculates overall score
    5. Generates detailed feedback

    Args:
        expected_chinese: What should have been said (Chinese characters)
        actual_chinese: What was actually said (from Whisper transcription)

    Returns:
        Dictionary with comprehensive assessment:
            - overall_match: bool (True if perfect)
            - score: float (0-100, percentage of correct phonetic components)
            - expected_pinyin: str (space-separated pinyin)
            - actual_pinyin: str (space-separated pinyin)
            - syllable_details: List[Dict] (detailed comparison for each syllable)
            - summary: str (human-readable feedback)

    Examples:
        >>> assess_pronunciation("`}", "`}")
        {
            'overall_match': True,
            'score': 100.0,
            'expected_pinyin': 'ni3 hao3',
            'actual_pinyin': 'ni3 hao3',
            'syllable_details': [...],
            'summary': ' Perfect pronunciation!'
        }

        >>> assess_pronunciation("�", "�")
        {
            'overall_match': False,
            'score': 66.7,
            'expected_pinyin': 'ma4',
            'actual_pinyin': 'ma1',
            'syllable_details': [...],
            'summary': 'Issues: 1 tone error(s)'
        }
    """
    # Convert to pinyin
    expected_pinyin = text_to_pinyin(expected_chinese, Style.TONE3)
    actual_pinyin = text_to_pinyin(actual_chinese, Style.TONE3)

    # Decompose into syllables
    expected_syllables = [decompose_pinyin(syl) for syl in expected_pinyin]
    actual_syllables = [decompose_pinyin(syl) for syl in actual_pinyin]

    # Handle length mismatch
    if len(expected_syllables) != len(actual_syllables):
        return {
            'overall_match': False,
            'score': 0.0,
            'expected_pinyin': ' '.join(expected_pinyin),
            'actual_pinyin': ' '.join(actual_pinyin),
            'syllable_details': [],
            'summary': f"Length mismatch: expected {len(expected_syllables)} syllables, "
                      f"got {len(actual_syllables)}"
        }

    # Compare syllable by syllable
    syllable_comparisons = []
    for i, (exp_syl, act_syl) in enumerate(zip(expected_syllables, actual_syllables)):
        comparison = compare_syllables(exp_syl, act_syl)
        comparison['position'] = i
        comparison['expected'] = exp_syl.full
        comparison['actual'] = act_syl.full
        syllable_comparisons.append(comparison)

    # Calculate overall score
    # Each syllable has 3 components: initial + final + tone
    total_components = len(expected_syllables) * 3
    correct_components = sum([
        comp['initial_match'] + comp['final_match'] + comp['tone_match']
        for comp in syllable_comparisons
    ])

    score = (correct_components / total_components) * 100 if total_components > 0 else 0
    overall_match = all(comp['match'] for comp in syllable_comparisons)

    return {
        'overall_match': overall_match,
        'score': round(score, 1),
        'expected_pinyin': ' '.join(expected_pinyin),
        'actual_pinyin': ' '.join(actual_pinyin),
        'syllable_details': syllable_comparisons,
        'summary': generate_feedback_summary(syllable_comparisons)
    }

# ABOUTME: Tests for pronunciation scoring and assessment functions
# ABOUTME: Covers pinyin decomposition, syllable comparison, and scoring logic
import pytest
from src.scoring import (
    decompose_pinyin,
    compare_syllables,
    generate_feedback_summary,
    assess_pronunciation,
    Syllable,
    INITIALS_SORTED,
    TONE_NAMES
)


class TestDecomposePinyin:
    """Tests for pinyin decomposition into initial, final, and tone."""

    def test_simple_syllable_with_initial(self):
        result = decompose_pinyin('ni3')
        assert result.full == 'ni3'
        assert result.initial == 'n'
        assert result.final == 'i'
        assert result.tone == '3'

    def test_syllable_with_two_letter_initial(self):
        result = decompose_pinyin('zhi1')
        assert result.full == 'zhi1'
        assert result.initial == 'zh'
        assert result.final == 'i'
        assert result.tone == '1'

    def test_syllable_with_complex_final(self):
        result = decompose_pinyin('hao3')
        assert result.full == 'hao3'
        assert result.initial == 'h'
        assert result.final == 'ao'
        assert result.tone == '3'

    def test_syllable_without_initial(self):
        result = decompose_pinyin('ai4')
        assert result.full == 'ai4'
        assert result.initial == ''
        assert result.final == 'ai'
        assert result.tone == '4'

    def test_syllable_with_neutral_tone(self):
        result = decompose_pinyin('ma')
        assert result.full == 'ma'
        assert result.initial == 'm'
        assert result.final == 'a'
        assert result.tone == '5'

    def test_syllable_with_tone_1(self):
        result = decompose_pinyin('ma1')
        assert result.tone == '1'

    def test_syllable_with_tone_2(self):
        result = decompose_pinyin('ma2')
        assert result.tone == '2'

    def test_syllable_with_tone_4(self):
        result = decompose_pinyin('ma4')
        assert result.tone == '4'

    def test_ch_initial(self):
        result = decompose_pinyin('chi1')
        assert result.initial == 'ch'
        assert result.final == 'i'

    def test_sh_initial(self):
        result = decompose_pinyin('shi4')
        assert result.initial == 'sh'
        assert result.final == 'i'

    def test_empty_string(self):
        result = decompose_pinyin('')
        assert result.full == ''
        assert result.initial == ''
        assert result.final == ''
        assert result.tone == '5'


class TestCompareSyllables:
    """Tests for comparing two syllables and identifying differences."""

    def test_perfect_match(self):
        exp = decompose_pinyin('ma1')
        act = decompose_pinyin('ma1')
        result = compare_syllables(exp, act)

        assert result['match'] is True
        assert result['initial_match'] is True
        assert result['final_match'] is True
        assert result['tone_match'] is True
        assert 'Correct' in result['feedback']

    def test_wrong_tone(self):
        exp = decompose_pinyin('ma1')
        act = decompose_pinyin('ma4')
        result = compare_syllables(exp, act)

        assert result['match'] is False
        assert result['initial_match'] is True
        assert result['final_match'] is True
        assert result['tone_match'] is False
        assert 'tone:' in result['feedback']

    def test_wrong_initial(self):
        exp = decompose_pinyin('ni3')
        act = decompose_pinyin('li3')
        result = compare_syllables(exp, act)

        assert result['match'] is False
        assert result['initial_match'] is False
        assert result['final_match'] is True
        assert result['tone_match'] is True
        assert 'initial:' in result['feedback']

    def test_wrong_final(self):
        exp = decompose_pinyin('hao3')
        act = decompose_pinyin('han3')
        result = compare_syllables(exp, act)

        assert result['match'] is False
        assert result['initial_match'] is True
        assert result['final_match'] is False
        assert result['tone_match'] is True
        assert 'final:' in result['feedback']

    def test_multiple_errors(self):
        exp = decompose_pinyin('ma1')
        act = decompose_pinyin('ba4')
        result = compare_syllables(exp, act)

        assert result['match'] is False
        assert result['initial_match'] is False
        assert result['final_match'] is True
        assert result['tone_match'] is False
        assert 'initial:' in result['feedback']
        assert 'tone:' in result['feedback']

    def test_everything_wrong(self):
        exp = decompose_pinyin('ma1')
        act = decompose_pinyin('ni3')
        result = compare_syllables(exp, act)

        assert result['match'] is False
        assert result['initial_match'] is False
        assert result['final_match'] is False
        assert result['tone_match'] is False


class TestGenerateFeedbackSummary:
    """Tests for generating human-readable feedback from comparisons."""

    def test_perfect_pronunciation(self):
        comparisons = [
            {'match': True, 'tone_match': True, 'initial_match': True, 'final_match': True},
            {'match': True, 'tone_match': True, 'initial_match': True, 'final_match': True}
        ]
        summary = generate_feedback_summary(comparisons)
        assert 'Perfect pronunciation!' in summary

    def test_single_tone_error(self):
        comparisons = [
            {'match': False, 'tone_match': False, 'initial_match': True, 'final_match': True},
            {'match': True, 'tone_match': True, 'initial_match': True, 'final_match': True}
        ]
        summary = generate_feedback_summary(comparisons)
        assert '1 tone error(s)' in summary
        assert 'Issues:' in summary

    def test_multiple_tone_errors(self):
        comparisons = [
            {'match': False, 'tone_match': False, 'initial_match': True, 'final_match': True},
            {'match': False, 'tone_match': False, 'initial_match': True, 'final_match': True}
        ]
        summary = generate_feedback_summary(comparisons)
        assert '2 tone error(s)' in summary

    def test_initial_error(self):
        comparisons = [
            {'match': False, 'tone_match': True, 'initial_match': False, 'final_match': True}
        ]
        summary = generate_feedback_summary(comparisons)
        assert '1 initial consonant error(s)' in summary

    def test_final_error(self):
        comparisons = [
            {'match': False, 'tone_match': True, 'initial_match': True, 'final_match': False}
        ]
        summary = generate_feedback_summary(comparisons)
        assert '1 vowel/final error(s)' in summary

    def test_mixed_errors(self):
        comparisons = [
            {'match': False, 'tone_match': False, 'initial_match': False, 'final_match': True},
            {'match': False, 'tone_match': True, 'initial_match': True, 'final_match': False}
        ]
        summary = generate_feedback_summary(comparisons)
        assert '1 tone error(s)' in summary
        assert '1 initial consonant error(s)' in summary
        assert '1 vowel/final error(s)' in summary


class TestAssessPronunciation:
    """Tests for complete pronunciation assessment."""

    def test_perfect_pronunciation_single_word(self):
        result = assess_pronunciation('你好', '你好')

        assert result['overall_match'] is True
        assert result['score'] == 100.0
        assert result['expected_pinyin'] == 'ni3 hao3'
        assert result['actual_pinyin'] == 'ni3 hao3'
        assert 'Perfect pronunciation!' in result['summary']
        assert len(result['syllable_details']) == 2

    def test_perfect_pronunciation_single_character(self):
        result = assess_pronunciation('好', '好')

        assert result['overall_match'] is True
        assert result['score'] == 100.0

    def test_wrong_tone_single_syllable(self):
        # 妈 (ma1) vs 骂 (ma4)
        result = assess_pronunciation('妈', '骂')

        assert result['overall_match'] is False
        assert result['score'] < 100.0
        # Should have 2 correct components (initial + final) out of 3
        assert result['score'] == 66.7
        assert 'tone error' in result['summary']

    def test_completely_different_word(self):
        result = assess_pronunciation('你好', '谢谢')

        assert result['overall_match'] is False
        assert result['score'] < 100.0

    def test_length_mismatch(self):
        result = assess_pronunciation('你好', '你')

        assert result['overall_match'] is False
        assert result['score'] == 0.0
        assert 'Length mismatch' in result['summary']
        assert 'expected 2 syllables' in result['summary']
        assert 'got 1' in result['summary']

    def test_syllable_details_structure(self):
        result = assess_pronunciation('你好', '你好')

        details = result['syllable_details']
        assert len(details) == 2

        for detail in details:
            assert 'position' in detail
            assert 'expected' in detail
            assert 'actual' in detail
            assert 'match' in detail
            assert 'initial_match' in detail
            assert 'final_match' in detail
            assert 'tone_match' in detail
            assert 'feedback' in detail

    def test_partial_match_calculates_score_correctly(self):
        # Test that score is based on component matches
        # If 1 out of 3 components is wrong, score should be 66.7%
        result = assess_pronunciation('妈', '骂')
        assert result['score'] == 66.7

    def test_multi_syllable_with_one_error(self):
        # 你好 (ni3 hao3) with one tone wrong
        result = assess_pronunciation('你好', '李好')

        assert result['overall_match'] is False
        # First syllable: 0/3 components match (ni3 vs li3 - different initial)
        # Wait, li3 has different initial but same final and tone
        # So: 2/3 + 3/3 = 5/6 = 83.3%
        assert result['score'] > 0
        assert result['score'] < 100


class TestConstants:
    """Tests for module constants."""

    def test_initials_sorted_has_two_letter_initials_first(self):
        # Two-letter initials should come before single-letter
        zh_index = INITIALS_SORTED.index('zh')
        z_index = INITIALS_SORTED.index('z')
        assert zh_index < z_index

    def test_tone_names_has_all_tones(self):
        assert '1' in TONE_NAMES
        assert '2' in TONE_NAMES
        assert '3' in TONE_NAMES
        assert '4' in TONE_NAMES
        assert '5' in TONE_NAMES

# ABOUTME: Tests for transcription utilities and text processing
# ABOUTME: Covers pinyin conversion, text normalization, and romanization detection
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from src.transcription import (
    get_openai_client,
    transcribe_whisper,
    text_to_pinyin,
    text_to_pinyin_display,
    convert_traditional_to_simplified,
    remove_punctuation,
    is_romanization,
    calculate_api_cost
)
from pypinyin import Style


class TestGetOpenAIClient:
    """Tests for OpenAI client initialization."""

    def test_client_created_with_api_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        client = get_openai_client()
        assert client is not None
        assert client.api_key == "test-key-123"

    def test_raises_error_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable not set"):
            get_openai_client()


class TestTranscribeWhisper:
    """Tests for Whisper transcription (mocked)."""

    def test_successful_transcription(self, tmp_path, mocker):
        # Create a temporary audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "你好"
        mock_response.language = "zh"
        mock_response.duration = 2.5
        mock_response.segments = [
            Mock(id=0, start=0.0, end=2.5, text="你好")
        ]

        mock_client.audio.transcriptions.create.return_value = mock_response

        result = transcribe_whisper(audio_file, client=mock_client)

        assert result['text'] == "你好"
        assert result['language'] == "zh"
        assert result['duration'] == 2.5
        assert len(result['segments']) == 1
        assert result['segments'][0]['text'] == "你好"

        # Verify API was called correctly
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs['model'] == "whisper-1"
        assert call_kwargs['language'] == "zh"
        assert call_kwargs['response_format'] == "verbose_json"

    def test_transcription_without_segments(self, tmp_path, mocker):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "你好"
        mock_response.language = "zh"
        mock_response.duration = 2.5
        mock_response.segments = None

        mock_client.audio.transcriptions.create.return_value = mock_response

        result = transcribe_whisper(audio_file, client=mock_client)

        assert result['segments'] is None

    def test_file_not_found(self, mocker):
        mock_client = Mock()
        nonexistent_file = Path("/nonexistent/file.wav")

        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            transcribe_whisper(nonexistent_file, client=mock_client)

    def test_custom_language_parameter(self, tmp_path, mocker):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "hello"
        mock_response.language = "en"
        mock_response.duration = 1.0
        mock_response.segments = []

        mock_client.audio.transcriptions.create.return_value = mock_response

        result = transcribe_whisper(audio_file, language="en", client=mock_client)

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs['language'] == "en"


class TestTextToPinyin:
    """Tests for Chinese to pinyin conversion."""

    def test_simple_conversion(self):
        result = text_to_pinyin("你好")
        assert result == ['ni3', 'hao3']

    def test_single_character(self):
        result = text_to_pinyin("好")
        assert result == ['hao3']

    def test_tone_variations(self):
        # 妈(ma1) 麻(ma2) 马(ma3) 骂(ma4)
        result = text_to_pinyin("妈麻马骂")
        assert len(result) == 4
        assert result[0] == 'ma1'
        assert result[1] == 'ma2'
        assert result[2] == 'ma3'
        assert result[3] == 'ma4'

    def test_empty_string(self):
        result = text_to_pinyin("")
        assert result == []

    def test_returns_list_of_strings(self):
        result = text_to_pinyin("你好")
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)


class TestTextToPinyinDisplay:
    """Tests for pinyin display with tone marks."""

    def test_display_format(self):
        result = text_to_pinyin_display("你好")
        # Should have tone marks (ǐ and ǎ)
        assert 'nǐ' in result
        assert 'hǎo' in result
        assert ' ' in result  # Space-separated

    def test_single_character(self):
        result = text_to_pinyin_display("好")
        assert 'hǎo' in result

    def test_returns_string(self):
        result = text_to_pinyin_display("你好")
        assert isinstance(result, str)


class TestConvertTraditionalToSimplified:
    """Tests for traditional to simplified Chinese conversion."""

    def test_traditional_to_simplified(self):
        # 繁體中文 (traditional) -> 繁体中文 (simplified)
        result = convert_traditional_to_simplified("繁體中文")
        assert result == "繁体中文"

    def test_already_simplified_unchanged(self):
        result = convert_traditional_to_simplified("你好")
        assert result == "你好"

    def test_mixed_content(self):
        # Mix of traditional and simplified
        result = convert_traditional_to_simplified("你好繁體")
        assert "繁体" in result

    def test_empty_string(self):
        result = convert_traditional_to_simplified("")
        assert result == ""


class TestRemovePunctuation:
    """Tests for punctuation removal."""

    def test_chinese_period(self):
        result = remove_punctuation("不对。")
        assert result == "不对"

    def test_chinese_comma(self):
        result = remove_punctuation("你好，世界")
        assert result == "你好世界"

    def test_chinese_exclamation(self):
        result = remove_punctuation("你好！")
        assert result == "你好"

    def test_chinese_question_mark(self):
        result = remove_punctuation("你好吗？")
        assert result == "你好吗"

    def test_english_punctuation(self):
        result = remove_punctuation("Hello, world!")
        assert result == "Helloworld"

    def test_chinese_quotation_marks(self):
        result = remove_punctuation('"你好"')
        assert result == "你好"

    def test_mixed_punctuation(self):
        result = remove_punctuation("你好，世界！")
        assert result == "你好世界"

    def test_parentheses(self):
        result = remove_punctuation("你好（世界）")
        assert result == "你好世界"

    def test_no_punctuation(self):
        result = remove_punctuation("你好")
        assert result == "你好"

    def test_whitespace_removed(self):
        result = remove_punctuation("你 好")
        assert result == "你好"

    def test_empty_string(self):
        result = remove_punctuation("")
        assert result == ""


class TestIsRomanization:
    """Tests for detecting romanized vs Chinese text."""

    def test_chinese_characters(self):
        assert is_romanization("你好") is False

    def test_romanized_text_uppercase(self):
        assert is_romanization("Ni Hao") is True

    def test_romanized_text_lowercase(self):
        assert is_romanization("ni hao") is True

    def test_mixed_chinese_and_english(self):
        # Has at least one Chinese character, so not romanization
        assert is_romanization("你好hello") is False

    def test_single_chinese_character(self):
        assert is_romanization("好") is False

    def test_empty_string(self):
        assert is_romanization("") is False

    def test_whitespace_only(self):
        assert is_romanization("   ") is False

    def test_numbers(self):
        assert is_romanization("123") is True

    def test_punctuation_only(self):
        assert is_romanization("!!!") is True


class TestCalculateAPICost:
    """Tests for API cost calculation."""

    def test_one_minute(self):
        cost = calculate_api_cost(60)
        assert cost == 0.006

    def test_thirty_seconds(self):
        cost = calculate_api_cost(30)
        assert cost == 0.003

    def test_two_minutes(self):
        cost = calculate_api_cost(120)
        assert cost == 0.012

    def test_zero_duration(self):
        cost = calculate_api_cost(0)
        assert cost == 0.0

    def test_fractional_seconds(self):
        cost = calculate_api_cost(90)  # 1.5 minutes
        assert cost == pytest.approx(0.009)

    def test_very_short_duration(self):
        cost = calculate_api_cost(1)  # 1 second
        assert cost == pytest.approx(0.0001, abs=0.00001)

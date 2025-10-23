# ABOUTME: Tests for evaluation orchestration and pipeline integration
# ABOUTME: Covers test case loading, cache management, and end-to-end evaluation flow
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.eval import (
    load_eval_metadata,
    load_cache,
    save_cache,
    run_single_evaluation,
    run_evaluation,
    DEFAULT_METADATA_FILE,
    DEFAULT_AUDIO_DIR,
    DEFAULT_CACHE_FILE
)


class TestLoadEvalMetadata:
    """Tests for loading evaluation metadata from YAML."""

    def test_load_valid_yaml(self, tmp_path):
        yaml_content = """
test_cases:
  - filename: test_001
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: correct
  - filename: test_002
    expected_chinese: 谢谢
    expected_pinyin: xie4 xie4
    error_type: wrong_tone
"""
        yaml_file = tmp_path / "test_metadata.yml"
        yaml_file.write_text(yaml_content)

        test_cases = load_eval_metadata(yaml_file)

        assert len(test_cases) == 2
        assert test_cases[0]['filename'] == 'test_001'
        assert test_cases[0]['expected_chinese'] == '你好'
        assert test_cases[1]['error_type'] == 'wrong_tone'

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Metadata file not found"):
            load_eval_metadata(Path("/nonexistent/metadata.yml"))

    def test_yaml_with_severity(self, tmp_path):
        yaml_content = """
test_cases:
  - filename: test_001
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: wrong_tone
    severity: major
"""
        yaml_file = tmp_path / "test_metadata.yml"
        yaml_file.write_text(yaml_content)

        test_cases = load_eval_metadata(yaml_file)

        assert test_cases[0]['severity'] == 'major'


class TestLoadCache:
    """Tests for loading transcription cache."""

    def test_load_existing_cache(self, tmp_path):
        cache_data = {
            "test_001": {
                "text": "你好",
                "language": "zh",
                "duration": 2.5
            }
        }

        cache_file = tmp_path / "cache.json"
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        cache = load_cache(cache_file)

        assert "test_001" in cache
        assert cache["test_001"]["text"] == "你好"

    def test_load_nonexistent_cache(self):
        cache = load_cache(Path("/nonexistent/cache.json"))
        assert cache == {}


class TestSaveCache:
    """Tests for saving transcription cache."""

    def test_save_cache_successfully(self, tmp_path):
        cache_data = {
            "test_001": {
                "text": "你好",
                "language": "zh",
                "duration": 2.5
            }
        }

        cache_file = tmp_path / "cache.json"
        save_cache(cache_data, cache_file)

        assert cache_file.exists()

        loaded = json.loads(cache_file.read_text())
        assert loaded["test_001"]["text"] == "你好"

    def test_save_cache_creates_directory(self, tmp_path):
        cache_file = tmp_path / "nested" / "dir" / "cache.json"
        cache_data = {"test": "data"}

        save_cache(cache_data, cache_file)

        assert cache_file.exists()
        assert cache_file.parent.exists()

    def test_save_cache_preserves_chinese(self, tmp_path):
        cache_data = {
            "test_001": {
                "text": "你好世界",
            }
        }

        cache_file = tmp_path / "cache.json"
        save_cache(cache_data, cache_file)

        content = cache_file.read_text(encoding='utf-8')
        assert "你好世界" in content


class TestRunSingleEvaluation:
    """Tests for running a single evaluation."""

    def test_successful_evaluation(self, tmp_path, mocker):
        # Create fake audio file
        audio_file = tmp_path / "test_001.wav"
        audio_file.write_bytes(b"fake audio")

        test_case = {
            'filename': 'test_001',
            'expected_chinese': '你好',
            'expected_pinyin': 'ni3 hao3',
            'error_type': 'correct'
        }

        # Mock transcribe_whisper
        mock_transcribe = mocker.patch('src.eval.transcribe_whisper')
        mock_transcribe.return_value = {
            'text': '你好',
            'language': 'zh',
            'duration': 2.5,
            'segments': []
        }

        # Mock assess_pronunciation
        mock_assess = mocker.patch('src.eval.assess_pronunciation')
        mock_assess.return_value = {
            'overall_match': True,
            'score': 100.0,
            'expected_pinyin': 'ni3 hao3',
            'actual_pinyin': 'ni3 hao3',
            'syllable_details': [],
            'summary': '✓ Perfect pronunciation!'
        }

        mock_client = Mock()
        cache = {}

        result = run_single_evaluation(test_case, tmp_path, mock_client, use_cache=False, cache=cache)

        assert result['filename'] == 'test_001'
        assert result['score'] == 100.0
        assert result['overall_match'] is True
        assert 'test_001' in cache  # Should be added to cache

    def test_audio_file_not_found(self, tmp_path):
        test_case = {
            'filename': 'nonexistent',
            'expected_chinese': '你好',
            'expected_pinyin': 'ni3 hao3',
            'error_type': 'correct'
        }

        mock_client = Mock()
        result = run_single_evaluation(test_case, tmp_path, mock_client)

        assert 'error' in result
        assert result['score'] == 0.0
        assert result['overall_match'] is False

    def test_uses_cache_when_available(self, tmp_path, mocker):
        audio_file = tmp_path / "test_001.wav"
        audio_file.write_bytes(b"fake audio")

        test_case = {
            'filename': 'test_001',
            'expected_chinese': '你好',
            'expected_pinyin': 'ni3 hao3',
            'error_type': 'correct'
        }

        cache = {
            'test_001': {
                'text': '你好',
                'language': 'zh',
                'duration': 2.5,
                'segments': []
            }
        }

        mock_transcribe = mocker.patch('src.eval.transcribe_whisper')
        mock_assess = mocker.patch('src.eval.assess_pronunciation')
        mock_assess.return_value = {
            'overall_match': True,
            'score': 100.0,
            'expected_pinyin': 'ni3 hao3',
            'actual_pinyin': 'ni3 hao3',
            'syllable_details': [],
            'summary': '✓ Perfect pronunciation!'
        }

        mock_client = Mock()

        result = run_single_evaluation(test_case, tmp_path, mock_client, use_cache=True, cache=cache)

        # Should NOT call transcribe_whisper
        mock_transcribe.assert_not_called()
        assert result['used_cache'] is True

    def test_handles_romanization(self, tmp_path, mocker):
        audio_file = tmp_path / "test_001.wav"
        audio_file.write_bytes(b"fake audio")

        test_case = {
            'filename': 'test_001',
            'expected_chinese': '你好',
            'expected_pinyin': 'ni3 hao3',
            'error_type': 'correct'
        }

        mock_transcribe = mocker.patch('src.eval.transcribe_whisper')
        mock_transcribe.return_value = {
            'text': 'Ni Hao',  # Romanization
            'language': 'zh',
            'duration': 2.5,
            'segments': []
        }

        mock_client = Mock()
        cache = {}

        result = run_single_evaluation(test_case, tmp_path, mock_client, use_cache=False, cache=cache)

        assert result['is_romanization'] is True
        assert result['score'] == 0.0
        assert 'romanization' in result['summary'].lower()

    def test_transcription_error_handling(self, tmp_path, mocker):
        audio_file = tmp_path / "test_001.wav"
        audio_file.write_bytes(b"fake audio")

        test_case = {
            'filename': 'test_001',
            'expected_chinese': '你好',
            'expected_pinyin': 'ni3 hao3',
            'error_type': 'correct'
        }

        mock_transcribe = mocker.patch('src.eval.transcribe_whisper')
        mock_transcribe.side_effect = Exception("API error")

        mock_client = Mock()

        result = run_single_evaluation(test_case, tmp_path, mock_client)

        assert 'error' in result
        assert 'Transcription failed' in result['error']
        assert result['score'] == 0.0


class TestRunEvaluation:
    """Tests for full evaluation pipeline."""

    def test_evaluation_with_no_test_cases(self, tmp_path, mocker, monkeypatch):
        # Create empty metadata file
        yaml_content = """
test_cases: []
"""
        yaml_file = tmp_path / "metadata.yml"
        yaml_file.write_text(yaml_content)

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        results = run_evaluation(metadata_file=yaml_file, audio_dir=tmp_path)

        assert results == []

    def test_evaluation_filters_by_error_type(self, tmp_path, mocker, monkeypatch):
        yaml_content = """
test_cases:
  - filename: test_correct
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: correct
  - filename: test_wrong_tone
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: wrong_tone
"""
        yaml_file = tmp_path / "metadata.yml"
        yaml_file.write_text(yaml_content)

        # Create fake audio files
        (tmp_path / "test_correct.wav").write_bytes(b"audio")
        (tmp_path / "test_wrong_tone.wav").write_bytes(b"audio")

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Mock the necessary functions
        mocker.patch('src.eval.transcribe_whisper', return_value={
            'text': '你好', 'language': 'zh', 'duration': 2.5, 'segments': []
        })
        mocker.patch('src.eval.assess_pronunciation', return_value={
            'overall_match': True, 'score': 100.0,
            'expected_pinyin': 'ni3 hao3', 'actual_pinyin': 'ni3 hao3',
            'syllable_details': [], 'summary': '✓ Perfect'
        })
        mocker.patch('src.eval.generate_console_report', return_value="Mock report")

        results = run_evaluation(
            metadata_file=yaml_file,
            audio_dir=tmp_path,
            error_type='wrong_tone'
        )

        # Should only evaluate the wrong_tone test case
        assert len(results) == 1
        assert results[0]['filename'] == 'test_wrong_tone'

    def test_evaluation_saves_csv_when_output_dir_specified(self, tmp_path, mocker, monkeypatch):
        yaml_content = """
test_cases:
  - filename: test_001
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: correct
"""
        yaml_file = tmp_path / "metadata.yml"
        yaml_file.write_text(yaml_content)

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "test_001.wav").write_bytes(b"audio")

        output_dir = tmp_path / "results"

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mocker.patch('src.eval.transcribe_whisper', return_value={
            'text': '你好', 'language': 'zh', 'duration': 2.5, 'segments': []
        })
        mocker.patch('src.eval.assess_pronunciation', return_value={
            'overall_match': True, 'score': 100.0,
            'expected_pinyin': 'ni3 hao3', 'actual_pinyin': 'ni3 hao3',
            'syllable_details': [], 'summary': '✓ Perfect'
        })
        mocker.patch('src.eval.generate_console_report', return_value="Mock report")

        results = run_evaluation(
            metadata_file=yaml_file,
            audio_dir=audio_dir,
            output_dir=output_dir
        )

        # Check that output directory was created and CSV was saved
        assert output_dir.exists()
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) == 1

    def test_evaluation_saves_cache(self, tmp_path, mocker, monkeypatch):
        yaml_content = """
test_cases:
  - filename: test_001
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: correct
"""
        yaml_file = tmp_path / "metadata.yml"
        yaml_file.write_text(yaml_content)

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "test_001.wav").write_bytes(b"audio")

        cache_file = tmp_path / "cache.json"

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mocker.patch('src.eval.transcribe_whisper', return_value={
            'text': '你好', 'language': 'zh', 'duration': 2.5, 'segments': []
        })
        mocker.patch('src.eval.assess_pronunciation', return_value={
            'overall_match': True, 'score': 100.0,
            'expected_pinyin': 'ni3 hao3', 'actual_pinyin': 'ni3 hao3',
            'syllable_details': [], 'summary': '✓ Perfect'
        })
        mocker.patch('src.eval.generate_console_report', return_value="Mock report")

        results = run_evaluation(
            metadata_file=yaml_file,
            audio_dir=audio_dir,
            cache_file=cache_file
        )

        # Cache file should have been created
        assert cache_file.exists()
        cache = json.loads(cache_file.read_text())
        assert 'test_001' in cache


class TestConstants:
    """Tests for module constants."""

    def test_default_paths_are_paths(self):
        assert isinstance(DEFAULT_METADATA_FILE, Path)
        assert isinstance(DEFAULT_AUDIO_DIR, Path)
        assert isinstance(DEFAULT_CACHE_FILE, Path)

    def test_default_paths_make_sense(self):
        assert "metadata" in str(DEFAULT_METADATA_FILE).lower()
        assert "audio" in str(DEFAULT_AUDIO_DIR).lower()
        assert "cache" in str(DEFAULT_CACHE_FILE).lower()

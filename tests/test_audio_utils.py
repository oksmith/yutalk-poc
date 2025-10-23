# ABOUTME: Tests for audio file utilities and helper functions
# ABOUTME: Covers file validation, path handling, and directory management
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.audio_utils import (
    validate_audio_file,
    get_audio_duration,
    get_audio_files,
    ensure_directory_exists,
    get_filename_without_extension,
    construct_audio_path,
)


class TestValidateAudioFile:
    """Tests for audio file validation."""

    def test_valid_wav_file(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(audio_file) is True

    def test_valid_mp3_file(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(audio_file) is True

    def test_valid_flac_file(self, tmp_path):
        audio_file = tmp_path / "test.flac"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(audio_file) is True

    def test_valid_ogg_file(self, tmp_path):
        audio_file = tmp_path / "test.ogg"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(audio_file) is True

    def test_valid_m4a_file(self, tmp_path):
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(audio_file) is True

    def test_nonexistent_file(self):
        assert validate_audio_file("/nonexistent/file.wav") is False

    def test_invalid_extension(self, tmp_path):
        text_file = tmp_path / "test.txt"
        text_file.write_text("not audio")

        assert validate_audio_file(text_file) is False

    def test_directory_not_file(self, tmp_path):
        directory = tmp_path / "audio_dir"
        directory.mkdir()

        assert validate_audio_file(directory) is False

    def test_case_insensitive_extension(self, tmp_path):
        audio_file = tmp_path / "test.WAV"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(audio_file) is True

    def test_accepts_string_path(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        assert validate_audio_file(str(audio_file)) is True


class TestGetAudioDuration:
    """Tests for getting audio file duration."""

    @patch('src.audio_utils.sf.info')
    def test_successful_duration_read(self, mock_info):
        mock_info.return_value = Mock(duration=3.5)

        duration = get_audio_duration("test.wav")

        assert duration == 3.5
        mock_info.assert_called_once_with("test.wav")

    @patch('src.audio_utils.sf.info')
    def test_file_read_error_returns_none(self, mock_info):
        mock_info.side_effect = Exception("Cannot read file")

        duration = get_audio_duration("invalid.wav")

        assert duration is None

    @patch('src.audio_utils.sf.info')
    def test_accepts_path_object(self, mock_info):
        mock_info.return_value = Mock(duration=2.0)

        duration = get_audio_duration(Path("test.wav"))

        assert duration == 2.0


class TestGetAudioFiles:
    """Tests for finding audio files in directories."""

    def test_finds_wav_files(self, tmp_path):
        # Create test files
        (tmp_path / "file1.wav").write_bytes(b"audio1")
        (tmp_path / "file2.wav").write_bytes(b"audio2")
        (tmp_path / "file3.txt").write_bytes(b"not audio")

        files = get_audio_files(tmp_path)

        assert len(files) == 2
        assert all(f.suffix == '.wav' for f in files)

    def test_custom_pattern(self, tmp_path):
        (tmp_path / "file1.wav").write_bytes(b"audio1")
        (tmp_path / "file2.mp3").write_bytes(b"audio2")

        files = get_audio_files(tmp_path, pattern="*.mp3")

        assert len(files) == 1
        assert files[0].suffix == '.mp3'

    def test_returns_sorted_list(self, tmp_path):
        (tmp_path / "c.wav").write_bytes(b"audio")
        (tmp_path / "a.wav").write_bytes(b"audio")
        (tmp_path / "b.wav").write_bytes(b"audio")

        files = get_audio_files(tmp_path)

        names = [f.name for f in files]
        assert names == ['a.wav', 'b.wav', 'c.wav']

    def test_nonexistent_directory(self):
        files = get_audio_files("/nonexistent/directory")
        assert files == []

    def test_empty_directory(self, tmp_path):
        files = get_audio_files(tmp_path)
        assert files == []

    def test_accepts_string_path(self, tmp_path):
        (tmp_path / "test.wav").write_bytes(b"audio")

        files = get_audio_files(str(tmp_path))

        assert len(files) == 1


class TestEnsureDirectoryExists:
    """Tests for directory creation."""

    def test_creates_new_directory(self, tmp_path):
        new_dir = tmp_path / "new_directory"

        result = ensure_directory_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_creates_nested_directories(self, tmp_path):
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        result = ensure_directory_exists(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_existing_directory_no_error(self, tmp_path):
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory_exists(existing_dir)

        assert result == existing_dir
        assert existing_dir.exists()

    def test_accepts_string_path(self, tmp_path):
        new_dir = tmp_path / "new_directory"

        result = ensure_directory_exists(str(new_dir))

        assert new_dir.exists()
        assert isinstance(result, Path)


class TestGetFilenameWithoutExtension:
    """Tests for extracting filename without extension."""

    def test_simple_filename(self):
        result = get_filename_without_extension("test.wav")
        assert result == "test"

    def test_with_path(self):
        result = get_filename_without_extension("data/audio/test.wav")
        assert result == "test"

    def test_multiple_dots_in_name(self):
        result = get_filename_without_extension("test.file.name.wav")
        assert result == "test.file.name"

    def test_path_object(self):
        result = get_filename_without_extension(Path("data/audio/test.wav"))
        assert result == "test"

    def test_complex_path(self):
        result = get_filename_without_extension("data/audio/eval_ni_hao_perfect_001.wav")
        assert result == "eval_ni_hao_perfect_001"


class TestConstructAudioPath:
    """Tests for constructing audio file paths."""

    def test_basic_construction(self):
        result = construct_audio_path("data/eval_audio", "test")

        assert result == Path("data/eval_audio/test.wav")

    def test_filename_with_extension_removed(self):
        result = construct_audio_path("data/eval_audio", "test.wav")

        assert result == Path("data/eval_audio/test.wav")

    def test_custom_extension(self):
        result = construct_audio_path("data/eval_audio", "test", extension=".mp3")

        assert result == Path("data/eval_audio/test.mp3")

    def test_extension_without_dot(self):
        result = construct_audio_path("data/eval_audio", "test", extension="mp3")

        assert result == Path("data/eval_audio/test.mp3")

    def test_path_objects(self):
        result = construct_audio_path(Path("data/eval_audio"), "test")

        assert result == Path("data/eval_audio/test.wav")

    def test_complex_filename(self):
        result = construct_audio_path(
            "data/eval_audio",
            "eval_ni_hao_perfect_001"
        )

        assert result == Path("data/eval_audio/eval_ni_hao_perfect_001.wav")


class TestRecordAudio:
    """Tests for audio recording (mocked, not actually recording)."""

    @patch('src.audio_utils.sd.rec')
    @patch('src.audio_utils.sd.wait')
    @patch('src.audio_utils.sf.write')
    def test_basic_recording(self, mock_write, mock_wait, mock_rec, tmp_path):
        import numpy as np
        mock_rec.return_value = np.zeros((48000, 1), dtype='float32')

        from src.audio_utils import record_audio
        audio_data, sample_rate = record_audio(
            duration=3,
            filename=None,
            sample_rate=16000
        )

        mock_rec.assert_called_once()
        mock_wait.assert_called_once()
        mock_write.assert_not_called()  # No filename provided
        assert sample_rate == 16000

    @patch('src.audio_utils.sd.rec')
    @patch('src.audio_utils.sd.wait')
    @patch('src.audio_utils.sf.write')
    def test_recording_with_save(self, mock_write, mock_wait, mock_rec, tmp_path):
        import numpy as np
        mock_rec.return_value = np.zeros((48000, 1), dtype='float32')

        from src.audio_utils import record_audio
        audio_data, sample_rate = record_audio(
            duration=3,
            filename="test_recording",
            output_dir=tmp_path,
            sample_rate=16000
        )

        mock_write.assert_called_once()
        # Check that the file path is correct
        call_args = mock_write.call_args[0]
        assert str(call_args[0]) == str(tmp_path / "test_recording.wav")


class TestPlayAudio:
    """Tests for audio playback (mocked)."""

    @patch('src.audio_utils.sf.read')
    @patch('src.audio_utils.sd.play')
    @patch('src.audio_utils.sd.wait')
    def test_play_single_file(self, mock_wait, mock_play, mock_read, tmp_path):
        import numpy as np

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_read.return_value = (np.zeros(16000), 16000)

        from src.audio_utils import play_audio
        play_audio(audio_file, wait=True)

        mock_read.assert_called_once()
        mock_play.assert_called_once()
        mock_wait.assert_called_once()

    @patch('src.audio_utils.sf.read')
    @patch('src.audio_utils.sd.play')
    @patch('src.audio_utils.sd.wait')
    def test_play_with_base_dir(self, mock_wait, mock_play, mock_read, tmp_path):
        import numpy as np

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_read.return_value = (np.zeros(16000), 16000)

        from src.audio_utils import play_audio
        play_audio("test", base_dir=tmp_path, wait=True)

        mock_read.assert_called_once()

    @patch('src.audio_utils.sf.read')
    @patch('src.audio_utils.sd.play')
    def test_play_without_wait(self, mock_play, mock_read, tmp_path):
        import numpy as np

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_read.return_value = (np.zeros(16000), 16000)

        from src.audio_utils import play_audio
        play_audio(audio_file, wait=False)

        mock_play.assert_called_once()

    def test_play_nonexistent_file_no_crash(self, capsys):
        from src.audio_utils import play_audio
        play_audio("/nonexistent/file.wav")

        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out


class TestRecordPhraseBatch:
    """Tests for batch phrase recording (mocked)."""

    @patch('src.audio_utils.record_audio')
    @patch('builtins.input')
    def test_batch_recording(self, mock_input, mock_record_audio, tmp_path):
        # Create a minimal YAML file
        yaml_content = """
test_cases:
  - filename: test_001
    expected_chinese: 你好
    expected_pinyin: ni3 hao3
    error_type: correct
    duration: 3
"""
        yaml_file = tmp_path / "test_metadata.yml"
        yaml_file.write_text(yaml_content)

        mock_input.return_value = ""  # Simulate Enter key

        from src.audio_utils import record_phrase_batch
        record_phrase_batch(yaml_file, output_dir=tmp_path)

        # Should call record_audio once for the single test case
        assert mock_record_audio.call_count == 1
        # Should prompt twice (initial prompt + per-case prompt)
        assert mock_input.call_count == 2

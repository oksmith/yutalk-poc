# ABOUTME: Tests for evaluation report generation and output formatting
# ABOUTME: Covers console reports, CSV export, and summary statistics
import pytest
from pathlib import Path
from datetime import datetime
from src.report import (
    generate_console_report,
    save_results_csv,
    generate_summary_stats,
    print_progress,
    create_timestamped_filename
)


class TestGenerateConsoleReport:
    """Tests for console report generation."""

    def test_basic_report_structure(self):
        results = [
            {
                'filename': 'test_001',
                'expected_chinese': '你好',
                'actual_chinese': '你好',
                'expected_pinyin': 'ni3 hao3',
                'actual_pinyin': 'ni3 hao3',
                'error_type': 'correct',
                'severity': None,
                'score': 100.0,
                'overall_match': True,
                'is_romanization': False,
                'summary': '✓ Perfect pronunciation!',
                'processing_time': 0.5
            }
        ]

        report = generate_console_report(results, total_duration=2.0, total_cost=0.001)

        assert "EVALUATION RESULTS" in report
        assert "Total Test Cases: 1" in report
        assert "Processing Time:" in report
        assert "API Cost:" in report
        assert "Average Score:" in report
        assert "Perfect Pronunciations:" in report

    def test_report_with_perfect_pronunciations(self):
        results = [
            {
                'filename': 'test_001',
                'error_type': 'correct',
                'score': 100.0,
                'overall_match': True,
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        report = generate_console_report(results, total_duration=2.0, total_cost=0.001)

        assert "100.0%" in report or "100%" in report
        assert "Perfect Pronunciations: 1/1" in report

    def test_report_with_errors(self):
        results = [
            {
                'filename': 'test_wrong_tone',
                'error_type': 'wrong_tone',
                'severity': 'major',
                'score': 66.7,
                'overall_match': False,
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        report = generate_console_report(results, total_duration=2.0, total_cost=0.001)

        assert "wrong_tone" in report
        assert "66.7%" in report

    def test_report_with_false_positives(self):
        results = [
            {
                'filename': 'test_correct',
                'expected_chinese': '你好',
                'actual_chinese': '你好',
                'expected_pinyin': 'ni3 hao3',
                'actual_pinyin': 'ni3 hao3',
                'error_type': 'correct',
                'score': 80.0,
                'overall_match': False,  # System incorrectly flagged as wrong
                'summary': 'Issues: 1 tone error',
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        report = generate_console_report(results, total_duration=2.0, total_cost=0.001)

        assert "False Positives" in report or "false positives" in report

    def test_report_with_missed_errors(self):
        results = [
            {
                'filename': 'test_wrong_tone',
                'expected_chinese': '妈',
                'actual_chinese': '骂',
                'expected_pinyin': 'ma1',
                'actual_pinyin': 'ma4',
                'error_type': 'wrong_tone',
                'severity': 'major',
                'score': 100.0,
                'overall_match': True,  # System missed the error
                'summary': '✓ Perfect pronunciation!',
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        report = generate_console_report(results, total_duration=2.0, total_cost=0.001)

        assert "MISSED errors" in report or "missed errors" in report.lower()

    def test_report_with_romanization(self):
        results = [
            {
                'filename': 'test_001',
                'error_type': 'correct',
                'score': 0.0,
                'overall_match': False,
                'is_romanization': True,
                'processing_time': 0.5,
                'summary': 'Romanization detected'
            }
        ]

        report = generate_console_report(results, total_duration=2.0, total_cost=0.001)

        assert "Romanization" in report

    def test_report_shows_overall_eval_score(self):
        results = [
            {
                'filename': 'test_correct',
                'error_type': 'correct',
                'score': 100.0,
                'overall_match': True,
                'is_romanization': False,
                'processing_time': 0.5
            },
            {
                'filename': 'test_wrong',
                'error_type': 'wrong_tone',
                'score': 66.7,
                'overall_match': False,
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        report = generate_console_report(results, total_duration=4.0, total_cost=0.002)

        assert "Overall Eval Score:" in report
        assert "Mispronunciation detection accuracy" in report

    def test_empty_results(self):
        results = []

        # Should not crash with empty results
        report = generate_console_report(results, total_duration=0, total_cost=0)
        assert "Total Test Cases: 0" in report
        assert "No test cases to report" in report


class TestSaveResultsCSV:
    """Tests for saving results to CSV."""

    def test_saves_csv_successfully(self, tmp_path):
        results = [
            {
                'filename': 'test_001',
                'error_type': 'correct',
                'severity': None,
                'score': 100.0,
                'overall_match': True,
                'expected_chinese': '你好',
                'actual_chinese': '你好',
                'expected_pinyin': 'ni3 hao3',
                'actual_pinyin': 'ni3 hao3',
                'summary': '✓ Perfect pronunciation!',
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        output_path = tmp_path / "results.csv"
        result_path = save_results_csv(results, output_path)

        assert result_path.exists()
        assert result_path == output_path

    def test_csv_contains_expected_columns(self, tmp_path):
        results = [
            {
                'filename': 'test_001',
                'error_type': 'correct',
                'severity': None,
                'score': 100.0,
                'overall_match': True,
                'expected_chinese': '你好',
                'actual_chinese': '你好',
                'expected_pinyin': 'ni3 hao3',
                'actual_pinyin': 'ni3 hao3',
                'summary': '✓ Perfect pronunciation!',
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        output_path = tmp_path / "results.csv"
        save_results_csv(results, output_path)

        content = output_path.read_text(encoding='utf-8')
        assert 'filename' in content
        assert 'error_type' in content
        assert 'score' in content
        assert 'overall_match' in content

    def test_csv_preserves_chinese_characters(self, tmp_path):
        results = [
            {
                'filename': 'test_001',
                'error_type': 'correct',
                'severity': None,
                'score': 100.0,
                'overall_match': True,
                'expected_chinese': '你好',
                'actual_chinese': '你好',
                'expected_pinyin': 'ni3 hao3',
                'actual_pinyin': 'ni3 hao3',
                'summary': '✓ Perfect pronunciation!',
                'is_romanization': False,
                'processing_time': 0.5
            }
        ]

        output_path = tmp_path / "results.csv"
        save_results_csv(results, output_path)

        content = output_path.read_text(encoding='utf-8')
        assert '你好' in content

    def test_accepts_string_path(self, tmp_path):
        results = [
            {
                'filename': 'test_001',
                'error_type': 'correct',
                'score': 100.0,
                'overall_match': True,
                'processing_time': 0.5
            }
        ]

        output_path = str(tmp_path / "results.csv")
        result_path = save_results_csv(results, output_path)

        assert Path(result_path).exists()


class TestGenerateSummaryStats:
    """Tests for generating summary statistics."""

    def test_basic_stats(self):
        results = [
            {
                'score': 100.0,
                'overall_match': True,
                'error_type': 'correct'
            },
            {
                'score': 66.7,
                'overall_match': False,
                'error_type': 'wrong_tone'
            }
        ]

        stats = generate_summary_stats(results)

        assert stats['total_cases'] == 2
        assert stats['average_score'] == pytest.approx(83.35, abs=0.1)
        assert stats['median_score'] == pytest.approx(83.35, abs=0.1)
        assert stats['min_score'] == 66.7
        assert stats['max_score'] == 100.0
        assert stats['perfect_count'] == 1
        assert stats['perfect_rate'] == 0.5

    def test_stats_by_error_type(self):
        results = [
            {
                'score': 100.0,
                'overall_match': True,
                'error_type': 'correct'
            },
            {
                'score': 66.7,
                'overall_match': False,
                'error_type': 'wrong_tone'
            },
            {
                'score': 50.0,
                'overall_match': False,
                'error_type': 'wrong_tone'
            }
        ]

        stats = generate_summary_stats(results)

        assert 'by_error_type' in stats
        assert 'correct' in stats['by_error_type']
        assert 'wrong_tone' in stats['by_error_type']

        correct_stats = stats['by_error_type']['correct']
        assert correct_stats['count'] == 1
        assert correct_stats['average_score'] == 100.0

        tone_stats = stats['by_error_type']['wrong_tone']
        assert tone_stats['count'] == 2
        assert tone_stats['average_score'] == pytest.approx(58.35, abs=0.5)

    def test_detection_rate_for_errors(self):
        results = [
            {
                'score': 66.7,
                'overall_match': False,
                'error_type': 'wrong_tone'
            },
            {
                'score': 100.0,
                'overall_match': True,  # Missed detection
                'error_type': 'wrong_tone'
            }
        ]

        stats = generate_summary_stats(results)

        tone_stats = stats['by_error_type']['wrong_tone']
        # 1 detected out of 2 = 50% detection rate
        assert tone_stats['detection_rate'] == 0.5

    def test_false_positive_rate_for_correct(self):
        results = [
            {
                'score': 100.0,
                'overall_match': True,
                'error_type': 'correct'
            },
            {
                'score': 80.0,
                'overall_match': False,  # False positive
                'error_type': 'correct'
            }
        ]

        stats = generate_summary_stats(results)

        correct_stats = stats['by_error_type']['correct']
        # 1 false positive out of 2 = 50% false positive rate
        assert correct_stats['false_positive_rate'] == 0.5


class TestPrintProgress:
    """Tests for progress printing."""

    def test_prints_progress_info(self, capsys):
        print_progress(1, 10, "test_file.wav")

        captured = capsys.readouterr()
        assert "1/10" in captured.out
        assert "10.0%" in captured.out
        assert "test_file.wav" in captured.out

    def test_custom_status(self, capsys):
        print_progress(5, 20, "test_file.wav", status="Analyzing")

        captured = capsys.readouterr()
        assert "5/20" in captured.out
        assert "Analyzing" in captured.out

    def test_percentage_calculation(self, capsys):
        print_progress(50, 100, "test_file.wav")

        captured = capsys.readouterr()
        assert "50.0%" in captured.out


class TestCreateTimestampedFilename:
    """Tests for creating timestamped filenames."""

    def test_basic_filename(self):
        filename = create_timestamped_filename("eval_results")

        assert filename.startswith("eval_results_")
        assert filename.endswith(".csv")
        assert len(filename) > len("eval_results_.csv")

    def test_custom_extension(self):
        filename = create_timestamped_filename("eval_results", extension=".json")

        assert filename.startswith("eval_results_")
        assert filename.endswith(".json")

    def test_extension_without_dot(self):
        filename = create_timestamped_filename("eval_results", extension="txt")

        assert filename.endswith(".txt")

    def test_timestamp_format(self):
        filename = create_timestamped_filename("test")

        # Extract timestamp part (should be YYYYMMDD_HHMMSS format)
        # e.g., test_20250122_143052.csv
        parts = filename.replace(".csv", "").split("_")
        assert len(parts) >= 3  # test, YYYYMMDD, HHMMSS

        date_part = parts[-2]
        time_part = parts[-1]

        assert len(date_part) == 8  # YYYYMMDD
        assert len(time_part) == 6  # HHMMSS
        assert date_part.isdigit()
        assert time_part.isdigit()

    def test_unique_filenames(self):
        # Two calls should produce different filenames (different timestamps)
        import time

        filename1 = create_timestamped_filename("test")
        time.sleep(1.1)  # Ensure at least 1 second passes
        filename2 = create_timestamped_filename("test")

        assert filename1 != filename2

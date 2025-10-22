"""
Evaluation report generation for the pronunciation assessment system.

This module provides functions to generate:
- Console reports with summary statistics
- CSV files with detailed results
- Failure analysis and recommendations
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


def generate_console_report(results: List[Dict], total_duration: float, total_cost: float) -> str:
    """
    Generate comprehensive console report from evaluation results.

    Args:
        results: List of evaluation result dictionaries
        total_duration: Total processing time in seconds
        total_cost: Total API cost in USD

    Returns:
        Formatted report string

    Example result dict structure:
        {
            'filename': 'eval_ni_hao_perfect_001',
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
    """
    df = pd.DataFrame(results)
    total_cases = len(results)

    report = []
    report.append("=" * 80)
    report.append("EVALUATION RESULTS")
    report.append("=" * 80)
    report.append("")

    # Overall metrics
    report.append(f"Total Test Cases: {total_cases}")
    report.append(f"Processing Time: {total_duration:.1f} seconds ({total_duration/60:.2f} minutes)")
    report.append(f"API Cost: ${total_cost:.4f}")
    if total_cases > 0:
        report.append(f"Average processing time per file: {total_duration/total_cases:.2f}s")
    report.append("")

    # Overall accuracy
    report.append("--- Overall Performance ---")
    report.append(f"Average Score: {df['score'].mean():.1f}%")
    report.append(f"Median Score: {df['score'].median():.1f}%")
    report.append(f"Score Range: {df['score'].min():.1f}% - {df['score'].max():.1f}%")
    perfect_count = df['overall_match'].sum()
    report.append(f"Perfect Pronunciations: {perfect_count}/{total_cases} ({perfect_count/total_cases*100:.1f}%)")
    report.append("")

    # By error type
    report.append("--- Performance by Error Type ---")
    error_types = df.groupby('error_type')

    for error_type, group in error_types:
        n = len(group)
        avg_score = group['score'].mean()
        perfect = group['overall_match'].sum()

        report.append(f"\n{error_type} (n={n}):")
        report.append(f"  Average Score: {avg_score:.1f}%")
        report.append(f"  Perfect: {perfect}/{n} ({perfect/n*100:.1f}%)")

        if error_type == 'correct':
            # For correct pronunciation, report false positives
            false_positives = n - perfect
            if false_positives > 0:
                report.append(f"  ⚠ False Positives: {false_positives}/{n} ({false_positives/n*100:.1f}%)")
                report.append(f"    (System incorrectly flagged correct pronunciation as wrong)")
        else:
            # For error types, report detection rate
            detected = n - perfect
            report.append(f"  Detection Rate: {detected}/{n} ({detected/n*100:.1f}%)")
            if perfect > 0:
                report.append(f"  ⚠ Missed Errors: {perfect}/{n} ({perfect/n*100:.1f}%)")

    # Romanization fallbacks
    report.append("")
    report.append("--- Romanization Analysis ---")
    romanization_count = df['is_romanization'].sum() if 'is_romanization' in df else 0
    report.append(f"Romanization Fallbacks: {romanization_count}/{total_cases} ({romanization_count/total_cases*100:.1f}%)")
    if romanization_count > 0:
        report.append(f"  (Cases where Whisper couldn't transcribe to Chinese)")

    # Failure analysis
    report.append("")
    report.append("--- Failure Analysis ---")
    report.append("")

    # Find cases where system failed to detect errors
    failures = df[(df['error_type'] != 'correct') & (df['overall_match'] == True)]
    if len(failures) > 0:
        report.append(f"Cases where system MISSED errors ({len(failures)} total):")
        for _, row in failures.iterrows():
            report.append(f"  • {row['filename']}")
            report.append(f"    Expected error: {row['error_type']} ({row.get('severity', 'unknown')})")
            report.append(f"    Score: {row['score']}% (should be lower)")
            report.append(f"    Summary: {row['summary']}")
        report.append("")
    else:
        report.append("✓ No missed errors - system detected all intentional mistakes!")
        report.append("")

    # Find cases where system incorrectly flagged correct pronunciation
    false_positives = df[(df['error_type'] == 'correct') & (df['overall_match'] == False)]
    if len(false_positives) > 0:
        report.append(f"Cases where system INCORRECTLY flagged errors ({len(false_positives)} total):")
        for _, row in false_positives.iterrows():
            report.append(f"  • {row['filename']}")
            report.append(f"    Expected: Perfect (100%)")
            report.append(f"    Got: {row['score']}%")
            report.append(f"    Summary: {row['summary']}")
        report.append("")
    else:
        report.append("✓ No false positives - system correctly validated all perfect pronunciations!")
        report.append("")

    # Recommendations
    report.append("--- Recommendations ---")
    report.append("")

    # Calculate error type specific accuracy
    tone_errors = df[df['error_type'] == 'wrong_tone']
    if len(tone_errors) > 0:
        tone_detection = (len(tone_errors) - tone_errors['overall_match'].sum()) / len(tone_errors) * 100
        report.append(f"• Tone error detection: {tone_detection:.1f}%")
        if tone_detection < 80:
            report.append(f"  ⚠ Needs improvement - consider additional tone-specific tests")

    initial_errors = df[df['error_type'] == 'wrong_initial']
    if len(initial_errors) > 0:
        initial_detection = (len(initial_errors) - initial_errors['overall_match'].sum()) / len(initial_errors) * 100
        report.append(f"• Initial consonant error detection: {initial_detection:.1f}%")
        if initial_detection < 80:
            report.append(f"  ⚠ Needs improvement")

    final_errors = df[df['error_type'] == 'wrong_final']
    if len(final_errors) > 0:
        final_detection = (len(final_errors) - final_errors['overall_match'].sum()) / len(final_errors) * 100
        report.append(f"• Final/vowel error detection: {final_detection:.1f}%")
        if final_detection < 80:
            report.append(f"  ⚠ Needs improvement")

    if romanization_count > 5:
        report.append(f"• High romanization rate ({romanization_count} cases)")
        report.append(f"  → Consider implementing fuzzy matching for romanized output")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def save_results_csv(results: List[Dict], output_path: Path | str) -> Path:
    """
    Save evaluation results to CSV file.

    Args:
        results: List of evaluation result dictionaries
        output_path: Path to save CSV file

    Returns:
        Path to saved CSV file
    """
    df = pd.DataFrame(results)

    # Reorder columns for better readability
    column_order = [
        'filename',
        'error_type',
        'severity',
        'score',
        'overall_match',
        'expected_chinese',
        'actual_chinese',
        'expected_pinyin',
        'actual_pinyin',
        'summary',
        'is_romanization',
        'processing_time'
    ]

    # Only include columns that exist
    columns = [col for col in column_order if col in df.columns]
    df = df[columns]

    output_path = Path(output_path)
    df.to_csv(output_path, index=False, encoding='utf-8')

    return output_path


def generate_summary_stats(results: List[Dict]) -> Dict:
    """
    Generate summary statistics from evaluation results.

    Args:
        results: List of evaluation result dictionaries

    Returns:
        Dictionary with summary statistics
    """
    df = pd.DataFrame(results)

    stats = {
        'total_cases': len(results),
        'average_score': df['score'].mean(),
        'median_score': df['score'].median(),
        'min_score': df['score'].min(),
        'max_score': df['score'].max(),
        'perfect_count': df['overall_match'].sum(),
        'perfect_rate': df['overall_match'].mean(),
    }

    # By error type
    stats['by_error_type'] = {}
    for error_type, group in df.groupby('error_type'):
        stats['by_error_type'][error_type] = {
            'count': len(group),
            'average_score': group['score'].mean(),
            'detection_rate': (len(group) - group['overall_match'].sum()) / len(group) if error_type != 'correct' else None,
            'false_positive_rate': (len(group) - group['overall_match'].sum()) / len(group) if error_type == 'correct' else None
        }

    return stats


def print_progress(current: int, total: int, filename: str, status: str = "Processing"):
    """
    Print progress during evaluation.

    Args:
        current: Current iteration number (1-indexed)
        total: Total number of items
        filename: Current filename being processed
        status: Status message (default: "Processing")
    """
    progress = current / total * 100
    print(f"[{current}/{total}] ({progress:.1f}%) {status}: {filename}")


def create_timestamped_filename(base_name: str, extension: str = ".csv") -> str:
    """
    Create filename with timestamp.

    Args:
        base_name: Base filename without extension
        extension: File extension (default: ".csv")

    Returns:
        Filename with timestamp

    Examples:
        >>> create_timestamped_filename("eval_results")
        'eval_results_20250122_143052.csv'
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not extension.startswith('.'):
        extension = '.' + extension

    return f"{base_name}_{timestamp}{extension}"

#!/usr/bin/env python3
"""
Evaluation script for the pronunciation assessment system.

This script:
1. Loads test cases from eval_metadata.yml
2. Runs the full assessment pipeline on each audio file
3. Generates comprehensive evaluation reports
4. Saves results to CSV

Usage:
    # Run full eval suite
    uv run python src/eval.py

    # Run on specific error type only
    uv run python src/eval.py --error-type wrong_tone

    # Save detailed results
    uv run python src/eval.py --output results/

    # Skip API calls (use cached transcriptions if available)
    uv run python src/eval.py --use-cache
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from dotenv import load_dotenv

from .transcription import (
    transcribe_whisper,
    convert_traditional_to_simplified,
    is_romanization,
    calculate_api_cost,
    get_openai_client
)
from .scoring import assess_pronunciation
from .audio_utils import (
    validate_audio_file,
    construct_audio_path,
    ensure_directory_exists
)
from .report import (
    generate_console_report,
    save_results_csv,
    print_progress,
    create_timestamped_filename
)


# Default paths
DEFAULT_METADATA_FILE = Path("data/eval_metadata.yml")
DEFAULT_AUDIO_DIR = Path("data/eval_audio")
DEFAULT_CACHE_FILE = Path("data/eval_transcriptions_cache.json")
DEFAULT_OUTPUT_DIR = Path("results")


def load_eval_metadata(metadata_file: Path) -> List[Dict]:
    """
    Load evaluation metadata from YAML file.

    Args:
        metadata_file: Path to eval_metadata.yml

    Returns:
        List of test case dictionaries
    """
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data['test_cases']


def load_cache(cache_file: Path) -> Dict:
    """
    Load cached transcriptions from JSON file.

    Args:
        cache_file: Path to cache file

    Returns:
        Dictionary mapping filename to transcription result
    """
    if not cache_file.exists():
        return {}

    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_cache(cache: Dict, cache_file: Path):
    """
    Save transcriptions to cache file.

    Args:
        cache: Dictionary mapping filename to transcription result
        cache_file: Path to cache file
    """
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def run_single_evaluation(
    test_case: Dict,
    audio_dir: Path,
    client,
    use_cache: bool = False,
    cache: Optional[Dict] = None
) -> Dict:
    """
    Run evaluation on a single test case.

    Args:
        test_case: Test case metadata dictionary
        audio_dir: Directory containing audio files
        client: OpenAI client instance
        use_cache: Whether to use cached transcriptions
        cache: Cache dictionary (if use_cache is True)

    Returns:
        Evaluation result dictionary
    """
    filename = test_case['filename']
    audio_path = construct_audio_path(audio_dir, filename)

    # Validate audio file exists
    if not validate_audio_file(audio_path):
        return {
            'filename': filename,
            'error': f'Audio file not found or invalid: {audio_path}',
            'score': 0.0,
            'overall_match': False
        }

    # Get transcription (from cache or API)
    start_time = time.time()

    if use_cache and cache and filename in cache:
        transcription_result = cache[filename]
        used_cache = True
    else:
        try:
            transcription_result = transcribe_whisper(audio_path, client=client)
            used_cache = False

            # Add to cache
            if cache is not None:
                cache[filename] = transcription_result
        except Exception as e:
            return {
                'filename': filename,
                'error': f'Transcription failed: {str(e)}',
                'score': 0.0,
                'overall_match': False
            }

    processing_time = time.time() - start_time

    # Extract transcription
    actual_chinese = transcription_result['text']
    actual_chinese = convert_traditional_to_simplified(actual_chinese)

    # Check if romanization
    is_roman = is_romanization(actual_chinese)

    # Run pronunciation assessment
    expected_chinese = test_case['expected_chinese']

    if is_roman:
        # Can't assess romanization properly
        assessment_result = {
            'overall_match': False,
            'score': 0.0,
            'expected_pinyin': test_case['expected_pinyin'],
            'actual_pinyin': 'N/A (romanization)',
            'syllable_details': [],
            'summary': f'Whisper returned romanization: "{actual_chinese}" (cannot assess)'
        }
    else:
        assessment_result = assess_pronunciation(expected_chinese, actual_chinese)

    # Combine results
    result = {
        'filename': filename,
        'error_type': test_case['error_type'],
        'severity': test_case.get('severity'),
        'expected_chinese': expected_chinese,
        'actual_chinese': actual_chinese,
        'expected_pinyin': test_case['expected_pinyin'],
        'actual_pinyin': assessment_result['actual_pinyin'],
        'score': assessment_result['score'],
        'overall_match': assessment_result['overall_match'],
        'summary': assessment_result['summary'],
        'is_romanization': is_roman,
        'processing_time': processing_time,
        'used_cache': used_cache,
        'duration': transcription_result.get('duration', 0)
    }

    return result


def run_evaluation(
    metadata_file: Path = DEFAULT_METADATA_FILE,
    audio_dir: Path = DEFAULT_AUDIO_DIR,
    error_type: Optional[str] = None,
    output_dir: Optional[Path] = None,
    use_cache: bool = False,
    cache_file: Path = DEFAULT_CACHE_FILE
) -> List[Dict]:
    """
    Run full evaluation on all test cases.

    Args:
        metadata_file: Path to eval_metadata.yml
        audio_dir: Directory containing audio files
        error_type: Optional filter for specific error type
        output_dir: Optional directory to save results
        use_cache: Whether to use cached transcriptions
        cache_file: Path to cache file

    Returns:
        List of evaluation result dictionaries
    """
    # Load environment variables
    load_dotenv()

    # Load metadata
    print(f"Loading test cases from: {metadata_file}")
    test_cases = load_eval_metadata(metadata_file)

    # Filter by error type if specified
    if error_type:
        test_cases = [tc for tc in test_cases if tc['error_type'] == error_type]
        print(f"Filtered to {len(test_cases)} test cases with error_type='{error_type}'")

    if not test_cases:
        print("No test cases to evaluate!")
        return []

    print(f"Total test cases: {len(test_cases)}")
    print()

    # Load cache if requested
    cache = load_cache(cache_file) if use_cache else {}
    if use_cache:
        print(f"Loaded {len(cache)} cached transcriptions from: {cache_file}")
        print()

    # Initialize OpenAI client
    client = get_openai_client()

    # Run evaluations
    results = []
    total_duration = 0

    for i, test_case in enumerate(test_cases, 1):
        filename = test_case['filename']
        print_progress(i, len(test_cases), filename)

        result = run_single_evaluation(
            test_case,
            audio_dir,
            client,
            use_cache=use_cache,
            cache=cache
        )

        results.append(result)
        total_duration += result.get('duration', 0)

    # Save cache if we added new entries
    if not use_cache or len(cache) > 0:
        save_cache(cache, cache_file)
        print(f"\nSaved transcription cache to: {cache_file}")

    # Calculate costs
    total_cost = calculate_api_cost(total_duration)

    # Generate and print console report
    print("\n")
    report = generate_console_report(results, total_duration, total_cost)
    print(report)

    # Save results to CSV if output directory specified
    if output_dir:
        output_dir = ensure_directory_exists(output_dir)
        csv_filename = create_timestamped_filename("eval_results", ".csv")
        csv_path = output_dir / csv_filename

        save_results_csv(results, csv_path)
        print(f"\nDetailed results saved to: {csv_path}")

    return results


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Run pronunciation assessment evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full eval suite
  uv run python src/eval.py

  # Run on specific error type only
  uv run python src/eval.py --error-type wrong_tone

  # Save detailed results
  uv run python src/eval.py --output results/

  # Skip API calls (use cached transcriptions)
  uv run python src/eval.py --use-cache
        """
    )

    parser.add_argument(
        '--metadata',
        type=Path,
        default=DEFAULT_METADATA_FILE,
        help=f'Path to eval_metadata.yml (default: {DEFAULT_METADATA_FILE})'
    )

    parser.add_argument(
        '--audio-dir',
        type=Path,
        default=DEFAULT_AUDIO_DIR,
        help=f'Directory containing audio files (default: {DEFAULT_AUDIO_DIR})'
    )

    parser.add_argument(
        '--error-type',
        type=str,
        help='Filter to specific error type (e.g., wrong_tone, wrong_initial, correct)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        help='Directory to save results (creates timestamped CSV)'
    )

    parser.add_argument(
        '--use-cache',
        action='store_true',
        help='Use cached transcriptions to avoid redundant API calls'
    )

    parser.add_argument(
        '--cache-file',
        type=Path,
        default=DEFAULT_CACHE_FILE,
        help=f'Path to cache file (default: {DEFAULT_CACHE_FILE})'
    )

    args = parser.parse_args()

    # Run evaluation
    run_evaluation(
        metadata_file=args.metadata,
        audio_dir=args.audio_dir,
        error_type=args.error_type,
        output_dir=args.output,
        use_cache=args.use_cache,
        cache_file=args.cache_file
    )


if __name__ == '__main__':
    main()

# Pronunciation Assessment Evaluation System

This directory contains the evaluation system for testing the Mandarin pronunciation assessment pipeline on diverse test cases.

## Overview

The evaluation system:
- Loads test cases from `data/eval_metadata.yml` (52 test cases with various error types)
- Runs the full pipeline: Audio → Whisper API → Phoneme Assessment
- Calculates comprehensive metrics by error type
- Generates detailed evaluation reports
- Caches transcriptions to avoid redundant API calls

## Quick Start

### Run Full Evaluation

```bash
# Run all 52 test cases and save results
uv run python -m src.eval --output results
```

This will:
- Process all test cases in `data/eval_metadata.yml`
- Print a comprehensive console report
- Save detailed results to `results/eval_results_[timestamp].csv`
- Cache transcriptions to `data/eval_transcriptions_cache.json`

### Run with Cache (Skip API Calls)

```bash
# Use cached transcriptions (much faster, no API cost)
uv run python -m src.eval --use-cache --output results
```

### Filter by Error Type

```bash
# Test only tone errors
uv run python -m src.eval --error-type wrong_tone

# Test only correct pronunciations
uv run python -m src.eval --error-type correct

# Test only initial consonant errors
uv run python -m src.eval --error-type wrong_initial
```

### Available Error Types

- `correct` - Perfect pronunciation (baseline)
- `wrong_tone` - Incorrect tone (ma1 vs ma4)
- `wrong_initial` - Incorrect initial consonant (ni vs li)
- `wrong_final` - Incorrect final/vowel (an vs ang)
- `multiple_errors` - Multiple simultaneous issues
- `unclear` - Very poor pronunciation (tests romanization fallback)

## Project Structure

```
yutalk-poc/
├── src/
│   ├── transcription.py      # Whisper API integration and pinyin conversion
│   ├── scoring.py             # Phoneme-level pronunciation assessment
│   ├── audio_utils.py         # Audio file utilities
│   ├── eval.py                # Main evaluation script (CLI)
│   └── report.py              # Report generation
├── data/
│   ├── eval_audio/            # 52 test WAV files
│   ├── eval_metadata.yml      # Test case metadata
│   └── eval_transcriptions_cache.json  # Cached API results
├── results/                   # Evaluation reports (created on first run)
└── EVAL_README.md            # This file
```

## Understanding the Results

### Console Report

The console report includes:

**Overall Performance:**
- Total test cases processed
- Processing time and API cost
- Average, median, min, max scores
- Perfect pronunciation rate

**Performance by Error Type:**
- Detection rate for each error type
- False positive rate (incorrectly flagged correct pronunciations)
- False negative rate (missed actual errors)

**Failure Analysis:**
- Specific test cases where the system failed
- Cases where errors were missed
- Cases where correct pronunciation was incorrectly flagged

**Recommendations:**
- Accuracy metrics for tone, initial, and final error detection
- Suggestions for improvement

### CSV Output

The CSV file (`results/eval_results_[timestamp].csv`) contains one row per test case with columns:
- `filename` - Test case filename
- `error_type` - Type of error (or 'correct')
- `severity` - Error severity (slight, moderate, severe)
- `score` - Pronunciation score (0-100%)
- `expected_chinese` - What should have been said
- `actual_chinese` - What Whisper transcribed
- `expected_pinyin` - Expected pinyin
- `actual_pinyin` - Actual pinyin
- `summary` - Human-readable feedback
- `is_romanization` - Whether Whisper returned romanization
- `processing_time` - Time to process this file

## Key Metrics Explained

### Detection Rate
For error types (wrong_tone, wrong_initial, etc.):
- **Detection Rate** = (Cases correctly identified as errors) / (Total cases with that error type)
- **Example:** If 8/10 tone errors are detected, detection rate = 80%

### False Positive Rate
For correct pronunciations:
- **False Positive Rate** = (Perfect cases incorrectly flagged) / (Total perfect cases)
- **Example:** If 2/10 perfect pronunciations are flagged as errors, false positive rate = 20%

### Overall Score
Pronunciation score calculation:
- Each syllable has 3 components: **initial + final + tone**
- Score = (Correct components / Total components) × 100%
- **Example:** "你好" (2 syllables, 6 components total)
  - If tone is wrong on first syllable: 5/6 correct = 83.3%
  - If both tones wrong: 4/6 correct = 66.7%

## Known Issues & Findings

Based on current evaluation results:

### ✅ What Works Well
- **Initial consonant detection:** 100% accuracy (zh/ch, n/l, etc.)
- **Final/vowel detection:** 100% accuracy (an/ang, en/eng, etc.)

### ⚠️ What Needs Improvement
- **Tone error detection:** Only 25% accuracy
  - Whisper often ignores tone errors
  - Language model bias: prefers common words (妈 over 骂)
  - Tone sandhi cases cause confusion

### 🐛 Specific Issues
1. **Tone errors missed:** System scores 100% when tones are wrong
2. **Length mismatches:** Some test cases have pypinyin conversion issues
3. **Romanization fallback:** 3 cases fell back to romanization
4. **False positives:** 5 correct pronunciations incorrectly flagged

## Adding New Test Cases

1. **Record audio** in `data/eval_audio/` as WAV files
2. **Add metadata** to `data/eval_metadata.yml`:

```yaml
  - filename: eval_your_test_001
    expected_chinese: "你好"
    expected_pinyin: "ni3 hao3"
    pronunciation_target: "ni3 hao3"
    error_type: correct
    severity: null
    target_error: null
    notes: "Description of what you're testing"
    duration: 3
```

3. **Run evaluation:**
```bash
uv run python -m src.eval --output results
```

## Cost Estimate

- **Whisper API pricing:** $0.006 per minute
- **52 test cases (164 seconds total):** ~$0.016
- **With caching:** $0 (uses cached results)

## Iterative Workflow

1. Run evaluation: `uv run python -m src.eval --output results`
2. Analyze failures in console report and CSV
3. Modify scoring algorithm in `src/scoring.py`
4. Re-run with cache: `uv run python -m src.eval --use-cache --output results`
5. Compare new results to previous CSV files
6. Repeat until satisfactory

## CLI Options

```bash
uv run python -m src.eval [OPTIONS]

Options:
  --metadata PATH        Path to eval_metadata.yml (default: data/eval_metadata.yml)
  --audio-dir PATH       Directory with audio files (default: data/eval_audio)
  --error-type TYPE      Filter to specific error type
  --output PATH          Directory to save results CSV
  --use-cache            Use cached transcriptions (skip API calls)
  --cache-file PATH      Path to cache file (default: data/eval_transcriptions_cache.json)
```

## Module Usage

You can also use the modules programmatically:

```python
from src.transcription import transcribe_whisper, text_to_pinyin
from src.scoring import assess_pronunciation
from src.eval import run_evaluation

# Transcribe audio
result = transcribe_whisper("data/eval_audio/eval_ni_hao_perfect_001.wav")
print(result['text'])  # "你好"

# Assess pronunciation
assessment = assess_pronunciation("你好", "你好")
print(assessment['score'])  # 100.0

# Run full evaluation
results = run_evaluation(
    error_type='wrong_tone',
    use_cache=True,
    output_dir='results'
)
```

## Next Steps

After evaluation:
1. Review failure cases to identify patterns
2. Improve scoring algorithm based on findings
3. Consider alternative approaches for tone detection
4. Build Gradio demo interface for user testing

## Questions or Issues?

- Check evaluation report for specific failure cases
- Review `src/scoring.py` for assessment logic
- Examine `data/eval_metadata.yml` for test case details
- Inspect cached transcriptions in `data/eval_transcriptions_cache.json`

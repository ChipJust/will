#!/usr/bin/env python3
"""
Quality check for extracted markdown text.
Usage: uv run python tools/extract/quality.py <markdown_file>
       cat file.md | uv run python tools/extract/quality.py -

Outputs JSON with metrics and a composite score/verdict.
Exit 0 always — callers read the verdict field.
"""

import json
import re
import sys
from pathlib import Path
from statistics import median


def _parse_timestamp(ts: str) -> float:
    """VTT/SRT timestamp string → seconds."""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(parts[0])


def _score_component(value: float, bad_threshold: float, ok_threshold: float,
                     higher_is_better: bool = True) -> float:
    """Linear interpolation between bad (0) and ok (100)."""
    if higher_is_better:
        if value <= bad_threshold:
            return 0.0
        if value >= ok_threshold:
            return 100.0
        return (value - bad_threshold) / (ok_threshold - bad_threshold) * 100
    else:
        if value >= bad_threshold:
            return 0.0
        if value <= ok_threshold:
            return 100.0
        return (bad_threshold - value) / (bad_threshold - ok_threshold) * 100


def analyze(text: str) -> dict:
    lines = text.splitlines()
    nonempty_lines = [l for l in lines if l.strip()]

    # Word count
    tokens = text.split()
    word_count = len(tokens)

    # Valid word ratio: 2–20 chars, mostly alphabetic (≥60%)
    def is_valid_word(t):
        t = re.sub(r"[^\w]", "", t)
        if len(t) < 2 or len(t) > 20:
            return False
        alpha = sum(c.isalpha() for c in t)
        return alpha / len(t) >= 0.6

    valid_words = sum(1 for t in tokens if is_valid_word(t))
    valid_word_ratio = valid_words / word_count if word_count else 0.0

    # Median line length (non-empty lines)
    line_lengths = [len(l) for l in nonempty_lines]
    med_line_len = median(line_lengths) if line_lengths else 0

    # Noise ratio: non-ASCII or control chars / total chars
    total_chars = len(text)
    noise_chars = sum(
        1 for c in text
        if ord(c) > 127 or (ord(c) < 32 and c not in "\n\r\t")
    )
    noise_ratio = noise_chars / total_chars if total_chars else 0.0

    # Component scores (0–100)
    s_words = _score_component(word_count, 100, 400, higher_is_better=True)
    s_valid = _score_component(valid_word_ratio, 0.70, 0.82, higher_is_better=True)
    s_lines = _score_component(med_line_len, 25, 40, higher_is_better=True)
    s_noise = _score_component(noise_ratio, 0.08, 0.04, higher_is_better=False)

    score = round(
        0.15 * s_words +
        0.40 * s_valid +
        0.25 * s_lines +
        0.20 * s_noise
    )

    if score >= 75:
        verdict = "ok"
    elif score >= 50:
        verdict = "marginal"
    else:
        verdict = "bad"

    return {
        "word_count": word_count,
        "valid_word_ratio": round(valid_word_ratio, 3),
        "median_line_length": round(med_line_len, 1),
        "noise_ratio": round(noise_ratio, 4),
        "score": score,
        "verdict": verdict,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()

    print(json.dumps(analyze(text), indent=2))


if __name__ == "__main__":
    main()

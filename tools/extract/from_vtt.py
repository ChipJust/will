#!/usr/bin/env python3
"""
Convert a WebVTT subtitle file to clean markdown.
Usage: uv run python tools/extract/from_vtt.py <vtt_file>

Outputs markdown to stdout. Long pauses (>3s) between cues become section breaks (---).
Exit 0 on success, 1 on error.
"""

import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path


_TIMESTAMP_LINE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[.,]\d+)\s*-->\s*(\d{1,2}:\d{2}:\d{2}[.,]\d+)"
)
_TAG = re.compile(r"<[^>]+>")
_POSITION = re.compile(r"\s+(align|line|position|size):[^\s]+")


def _ts_to_seconds(ts: str) -> float:
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return int(parts[0]) * 60 + float(parts[1])


def _clean_line(line: str) -> str:
    line = _TAG.sub("", line)          # strip HTML tags
    line = _POSITION.sub("", line)     # strip VTT position cues
    return line.strip()


def parse_vtt(text: str, pause_threshold: float = 3.0) -> str:
    """Parse VTT text, return clean markdown string.

    Handles the YouTube progressive caption format, where each cue carries
    forward lines from the previous cue and adds new words incrementally.
    Only lines that are new relative to the previous cue are emitted.
    """
    lines = text.splitlines()
    i = 0

    # Skip WEBVTT header and any NOTE/STYLE blocks
    while i < len(lines) and not _TIMESTAMP_LINE.match(lines[i]):
        i += 1

    segments: list[dict] = []
    prev_cue_lines: set[str] = set()

    while i < len(lines):
        m = _TIMESTAMP_LINE.match(lines[i])
        if not m:
            i += 1
            continue

        start = _ts_to_seconds(m.group(1))
        end = _ts_to_seconds(m.group(2))
        i += 1

        raw_lines = []
        while i < len(lines) and lines[i].strip() and not _TIMESTAMP_LINE.match(lines[i]):
            cleaned = _clean_line(lines[i])
            if cleaned:
                raw_lines.append(cleaned)
            i += 1

        # YouTube progressive format: only keep lines not seen in the previous cue
        new_lines = [l for l in raw_lines if l not in prev_cue_lines]
        prev_cue_lines = set(raw_lines)

        if new_lines:
            segments.append({"start": start, "end": end, "text": " ".join(new_lines)})

    if not segments:
        print("No cues found in VTT file.", file=sys.stderr)
        sys.exit(1)

    # Merge into paragraphs; insert --- on long pauses
    out_parts: list[str] = []
    buffer: list[str] = []
    prev_end: float = segments[0]["end"]

    for seg in segments:
        gap = seg["start"] - prev_end
        if gap > pause_threshold and buffer:
            out_parts.append(" ".join(buffer))
            out_parts.append("---")
            buffer = []
        buffer.append(seg["text"])
        prev_end = seg["end"]

    if buffer:
        out_parts.append(" ".join(buffer))

    return "\n\n".join(out_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: from_vtt.py <vtt_file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8", errors="replace")
    result = parse_vtt(text)
    print(result)


if __name__ == "__main__":
    main()

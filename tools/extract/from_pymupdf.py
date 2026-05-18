#!/usr/bin/env python3
"""
Extract text from a PDF as markdown using pymupdf4llm (primary method).
Usage: uv run python tools/extract/from_pymupdf.py <pdf_file>

Outputs markdown to stdout. Exit 0 on success, 1 on error.
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("pymupdf4llm not found. Run 'uv sync' first.", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: from_pymupdf.py <pdf_file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        md = pymupdf4llm.to_markdown(str(path))
        print(md)
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

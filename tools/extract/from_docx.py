#!/usr/bin/env python3
"""
Convert a DOCX file to markdown using pypandoc.
Usage: uv run python tools/extract/from_docx.py <docx_file>

Outputs markdown to stdout. Exit 0 on success, 1 on error.
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path

try:
    import pypandoc
except ImportError:
    print("pypandoc not found. Run 'uv sync' first.", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: from_docx.py <docx_file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        md = pypandoc.convert_file(str(path), "md")
        print(md)
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

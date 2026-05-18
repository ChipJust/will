#!/usr/bin/env python3
"""
Extract text from a PDF as markdown using pdfminer.six (fallback method).
Usage: uv run python tools/extract/from_pdfminer.py <pdf_file>

Uses a different extraction engine than from_pymupdf.py — sometimes handles
two-column layouts and unusual encodings better. Outputs markdown to stdout.
Exit 0 on success, 1 on error.
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTAnon
except ImportError:
    print("pdfminer.six not found. Run 'uv sync' first.", file=sys.stderr)
    sys.exit(1)


def _box_text(element) -> str:
    """Extract and clean text from a text box."""
    lines = []
    for line in element:
        if isinstance(line, LTTextLine):
            text = "".join(
                c.get_text() for c in line
                if not isinstance(c, LTAnon)
            ).strip()
            if text:
                lines.append(text)
    return " ".join(lines)


def extract_markdown(path: str) -> str:
    laparams = LAParams(
        line_margin=0.5,
        word_margin=0.1,
        char_margin=2.0,
        boxes_flow=0.5,   # 0.5 = balanced h/v flow; helps with columns
    )

    pages: list[str] = []
    for page_layout in extract_pages(path, laparams=laparams):
        boxes = []
        for element in page_layout:
            if isinstance(element, LTTextBox):
                text = _box_text(element)
                if text:
                    boxes.append(text)
        if boxes:
            pages.append("\n\n".join(boxes))

    return "\n\n---\n\n".join(pages)


def main():
    if len(sys.argv) < 2:
        print("Usage: from_pdfminer.py <pdf_file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        md = extract_markdown(str(path))
        print(md)
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

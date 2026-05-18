#!/usr/bin/env python3
"""
Extract article body from a URL or local HTML file using trafilatura.
Usage: uv run python tools/extract/from_html.py <url_or_html_file>

Strips navigation, ads, and boilerplate; returns the article body as markdown.
Outputs markdown to stdout. Exit 0 on success, 1 on error.
"""

import sys
import io
from pathlib import Path

# Ensure stdout uses UTF-8 regardless of the terminal's default encoding (e.g. cp1252 on Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import trafilatura
except ImportError:
    print("trafilatura not found. Run 'uv sync' first.", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: from_html.py <url_or_html_file>", file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    raw_html: str | None = None

    if source.startswith("http://") or source.startswith("https://"):
        raw_html = trafilatura.fetch_url(source)
        if not raw_html:
            print(f"Failed to fetch URL: {source}", file=sys.stderr)
            sys.exit(1)
    else:
        path = Path(source)
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        raw_html = path.read_text(encoding="utf-8", errors="replace")

    result = trafilatura.extract(
        raw_html,
        output_format="markdown",
        include_tables=True,
        include_links=False,   # skip href clutter
        no_fallback=False,
    )

    if not result:
        print("No article content extracted.", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()

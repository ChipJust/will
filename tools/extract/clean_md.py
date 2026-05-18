#!/usr/bin/env python3
"""
Strip repeating noise (page headers, footers, email cruft) from extracted markdown.
Usage: uv run python tools/extract/clean_md.py [source] [--profile NAME] [--list-profiles]

Input: markdown from `source` file, or stdin if source is omitted or '-'.
Output: cleaned markdown to stdout.
       JSON summary written as the LAST line of stderr, e.g.
       {"profiles": ["gmail-print"], "removed": {"timestamp": 18, "page_url": 18, ...}}
       When no profile activates: {"profiles": [], "removed": {}}.

Auto-detection: each profile carries a `signature` regex. If signature match
count >= `signature_threshold` across the input, the profile activates and
its `line_patterns` are deleted line-by-line. Multiple profiles can stack.

To handle a new source format: add a new entry to PROFILES below. The skill
ingest-paper instructs the agent to extend this dict rather than hand-editing
ingested markdown.
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


PROFILES: dict[str, dict] = {
    "gmail-print": {
        "description": (
            "Gmail email-export PDFs. Per-page footer = timestamp + permalink + "
            "N/N page number; first page also has To/From/Date/View-in-browser headers; "
            "subject line repeats on every page."
        ),
        "signature": re.compile(r"mail\.google\.com/mail|permmsgid=msg-f"),
        "signature_threshold": 2,
        "line_patterns": {
            "timestamp": re.compile(
                r"^\s*\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s+[AP]M\s*$"
            ),
            "page_url": re.compile(r"^\s*https://mail\.google\.com/\S*\s*$"),
            "page_number": re.compile(r"^\s*\d{1,3}/\d{1,3}\s*$"),
            "subject_repeat": re.compile(r"^\s*Gmail - .+$"),
            "view_in_browser": re.compile(r"^\s*View in browser\s*$"),
            "recipient_header": re.compile(
                r"^\s*\*\*[^*]+<[^>]+@[^>]+>\*\*\s*$"
            ),
            "from_to_header": re.compile(
                r"^\s*\*\*[^*]+\*\*\s*<[^>]+@[^>]+>\s*To:\s+\S+@\S+\s*$"
            ),
            "date_header": re.compile(
                r"^\s*[A-Z][a-z]{2,3},\s+[A-Z][a-z]{2,4}\s+\d{1,2},\s+\d{4}\s+at\s+"
                r"\d{1,2}:\d{2}\s+[AP]M\s*$"
            ),
        },
    },
}


def clean(text: str, profile_name: str | None = None) -> tuple[str, dict]:
    """Returns (cleaned_text, summary_dict).

    summary_dict shape:
        {"profiles": [name, ...], "removed": {pattern_name: count, ...}}
    """
    activated: list[str] = []

    if profile_name:
        if profile_name not in PROFILES:
            raise ValueError(f"Unknown profile: {profile_name}")
        activated = [profile_name]
    else:
        for name, prof in PROFILES.items():
            sig_count = len(prof["signature"].findall(text))
            if sig_count >= prof["signature_threshold"]:
                activated.append(name)

    if not activated:
        return text, {"profiles": [], "removed": {}}

    removed: dict[str, int] = {}
    lines = text.splitlines()

    for prof_name in activated:
        patterns = PROFILES[prof_name]["line_patterns"]
        kept: list[str] = []
        for line in lines:
            matched = None
            for pat_name, pat_re in patterns.items():
                if pat_re.match(line):
                    matched = pat_name
                    break
            if matched:
                removed[matched] = removed.get(matched, 0) + 1
            else:
                kept.append(line)
        lines = kept

    # Collapse runs of 3+ blank lines to 2 (deletion of cruft tends to leave gaps).
    collapsed: list[str] = []
    blank_run = 0
    for line in lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 2:
                collapsed.append(line)
        else:
            blank_run = 0
            collapsed.append(line)

    return "\n".join(collapsed), {"profiles": activated, "removed": removed}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Strip repeating noise from extracted markdown."
    )
    ap.add_argument(
        "source", nargs="?", default="-",
        help="Markdown file path, or '-' for stdin (default).",
    )
    ap.add_argument(
        "--profile", help="Force a specific profile (skip auto-detect)."
    )
    ap.add_argument(
        "--list-profiles", action="store_true",
        help="List known profiles and exit.",
    )
    args = ap.parse_args()

    if args.list_profiles:
        for name, prof in PROFILES.items():
            print(f"{name}: {prof['description']}")
        return

    if args.source == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.source).read_text(encoding="utf-8")

    cleaned, summary = clean(text, args.profile)
    sys.stdout.write(cleaned)
    print(json.dumps(summary), file=sys.stderr)


if __name__ == "__main__":
    main()

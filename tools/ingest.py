#!/usr/bin/env python3
"""ingest.py — Convert a source (PDF, DOCX, VTT, HTML file, URL, or YouTube link) to clean markdown in research/refs/.

Single source of truth for the ingest pipeline. Consumed by health, money,
home (and any future repo) via the `ingest-paper` skill. Each repo invokes:

    uv run --project D:/_code/will python D:/_code/will/tools/ingest.py <source>

Output is written to `<cwd>/research/refs/<slug>.md` — i.e. relative to the
caller's working directory. Extractor scripts are located next to this file
via Path(__file__).parent so the cwd can be anywhere.

Usage:
    uv run python D:/_code/will/tools/ingest.py <source> [options]

<source> can be:
  - path to a PDF, DOCX, VTT, or HTML file
  - a URL (treated as HTML, unless path ends in .pdf — auto-downloads and routes to pymupdf)
  - a YouTube URL (auto-fetches title + downloads transcript via yt-dlp, then cleans up)

Options:
  --slug SLUG          Output filename stem (default: derived from title or filename)
  --title TITLE        Override the title in the output header
  --force-method M     Skip auto-detection; use one of: pymupdf, pdfminer, docx, html, vtt

The cleanup pass auto-detects profiles in tools/extract/clean_md.py by
signature regex; when one activates, its `line_patterns` are stripped and
the YAML header gains `cleaned_with: <profile>`. For VTT (transcripts),
cleanup and quality checks are skipped.

Inputs:  one source string (path or URL).
Outputs: stderr status lines; saved markdown at <cwd>/research/refs/<slug>.md.
"""

import io
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

YOUTUBE_DOMAINS = ("youtube.com/", "youtu.be/")

# Extractors live next to this script; output is cwd-relative.
SCRIPT_DIR = Path(__file__).resolve().parent
EXTRACT_DIR = SCRIPT_DIR / "extract"
RESEARCH_DIR = Path("research/refs")

EXTRACTORS = {
    "pymupdf":  EXTRACT_DIR / "from_pymupdf.py",
    "pdfminer": EXTRACT_DIR / "from_pdfminer.py",
    "docx":     EXTRACT_DIR / "from_docx.py",
    "html":     EXTRACT_DIR / "from_html.py",
    "vtt":      EXTRACT_DIR / "from_vtt.py",
}

DEFAULT_METHOD = {
    ".pdf":  "pymupdf",
    ".docx": "docx",
    ".doc":  "docx",
    ".vtt":  "vtt",
    ".html": "html",
    ".htm":  "html",
}


def is_youtube_url(source: str) -> bool:
    return any(d in source for d in YOUTUBE_DOMAINS)


def download_youtube_vtt(url: str) -> Path:
    """Download YouTube auto-generated transcript as VTT. Returns path to file."""
    tmp_stem = "_yt_tmp"
    result = subprocess.run(
        ["yt-dlp", "--no-warnings", "--write-auto-sub", "--skip-download",
         "--sub-format", "vtt", "-o", tmp_stem, url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"yt-dlp failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    candidates = sorted(Path(".").glob(f"{tmp_stem}*.vtt"))
    if not candidates:
        print("yt-dlp ran but no VTT file was produced.", file=sys.stderr)
        sys.exit(1)
    return candidates[0]


def get_youtube_title(url: str) -> str | None:
    """Fetch human-readable title via yt-dlp. Returns None on failure."""
    result = subprocess.run(
        ["yt-dlp", "--no-warnings", "--get-title", url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    title = result.stdout.strip()
    return title or None


def is_pdf_url(source: str) -> bool:
    if not (source.startswith("http://") or source.startswith("https://")):
        return False
    return urlparse(source).path.lower().endswith(".pdf")


def download_pdf(url: str) -> Path:
    """Download a PDF from a URL to a temp file. Returns path to file."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    tmp_path = Path("_ingest_tmp.pdf")
    with urlopen(req) as resp, open(tmp_path, "wb") as f:
        f.write(resp.read())
    return tmp_path


def detect_method(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        return "html"
    suffix = Path(source).suffix.lower()
    if suffix not in DEFAULT_METHOD:
        print(f"Unknown file type '{suffix}'. Use --force-method.", file=sys.stderr)
        sys.exit(1)
    return DEFAULT_METHOD[suffix]


def run_extractor(method: str, source: str) -> str:
    script = EXTRACTORS[method]
    result = subprocess.run(
        [sys.executable, str(script), source],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        print(f"Extractor [{method}] failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def run_cleanup(text: str) -> tuple[str, list[str]]:
    """Run clean_md.py over the extracted text. Returns (cleaned_text, activated_profiles)."""
    script = EXTRACT_DIR / "clean_md.py"
    result = subprocess.run(
        [sys.executable, str(script), "-"],
        input=text, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        print(f"clean_md failed (continuing with raw):\n{result.stderr.strip()}", file=sys.stderr)
        return text, []
    # clean_md prints a JSON summary as the last stderr line.
    profiles: list[str] = []
    if result.stderr.strip():
        last = result.stderr.strip().splitlines()[-1]
        try:
            summary = json.loads(last)
            profiles = summary.get("profiles", []) or []
            removed = summary.get("removed", {}) or {}
            if profiles:
                counts = ", ".join(f"{k}={v}" for k, v in removed.items())
                print(f"Cleaned: profile={','.join(profiles)} removed: {counts}", file=sys.stderr)
        except json.JSONDecodeError:
            pass
    return result.stdout, profiles


def run_quality(text: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(EXTRACT_DIR / "quality.py"), "-"],
        input=text, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        return {"score": 0, "verdict": "bad", "error": result.stderr.strip()}
    return json.loads(result.stdout)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text.strip())
    return text[:80].rstrip("-")


def extract_title(md_text: str) -> str | None:
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def build_header(title: str, source: str, method: str, quality: dict,
                 source_url_override: str = "", cleaned_with: list[str] | None = None) -> str:
    is_url = source.startswith("http://") or source.startswith("https://")
    source_url = source_url_override or (source if is_url else "")
    source_file = "" if (is_url or source_url_override) else Path(source).name

    lines = ["---", f'title: "{title}"']
    if source_file:
        lines.append(f"source_file: {source_file}")
    if source_url:
        lines.append(f"source_url: {source_url}")
    lines.append(f"ingest_date: {date.today()}")
    lines.append(f"ingest_method: {method}")
    lines.append(f"quality_score: {quality.get('score', '?')}")
    if cleaned_with:
        lines.append(f"cleaned_with: {','.join(cleaned_with)}")
    lines.append("---")
    return "\n".join(lines)


def parse_args():
    args = sys.argv[1:]
    source = slug = title = force_method = None
    i = 0
    while i < len(args):
        if args[i] == "--slug" and i + 1 < len(args):
            slug = args[i + 1]; i += 2
        elif args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]; i += 2
        elif args[i] == "--force-method" and i + 1 < len(args):
            force_method = args[i + 1]; i += 2
        elif not args[i].startswith("--"):
            source = args[i]; i += 1
        else:
            i += 1
    if not source:
        print(__doc__)
        sys.exit(1)
    return source, slug, title, force_method


def main():
    source, slug, title_override, force_method = parse_args()

    youtube_url = ""
    pdf_url = ""
    tmp_vtt: Path | None = None
    tmp_pdf: Path | None = None
    if is_youtube_url(source):
        youtube_url = source
        if title_override is None:
            print("Fetching YouTube title via yt-dlp...", file=sys.stderr)
            title_override = get_youtube_title(source)
            if title_override:
                print(f"  title: {title_override}", file=sys.stderr)
        print("YouTube URL detected — downloading transcript via yt-dlp...", file=sys.stderr)
        tmp_vtt = download_youtube_vtt(source)
        source = str(tmp_vtt)
        force_method = force_method or "vtt"
    elif is_pdf_url(source):
        pdf_url = source
        print("PDF URL detected — downloading...", file=sys.stderr)
        tmp_pdf = download_pdf(source)
        source = str(tmp_pdf)
        force_method = force_method or "pymupdf"

    method = force_method or detect_method(source)
    if method not in EXTRACTORS:
        print(f"Unknown method '{method}'. Choose from: {', '.join(EXTRACTORS)}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting with [{method}]...", file=sys.stderr)
    md_text = run_extractor(method, source)

    if tmp_vtt and tmp_vtt.exists():
        tmp_vtt.unlink()
    if tmp_pdf and tmp_pdf.exists():
        tmp_pdf.unlink()

    # Skip cleanup + quality for VTT — transcripts are inherently clean and
    # don't have the page-header noise clean_md targets.
    cleaned_with: list[str] = []
    if method != "vtt":
        md_text, cleaned_with = run_cleanup(md_text)

    quality = run_quality(md_text)
    print(
        f"Quality: score={quality['score']} verdict={quality['verdict']} "
        f"words={quality.get('word_count','?')} valid_ratio={quality.get('valid_word_ratio','?')}",
        file=sys.stderr,
    )

    title = title_override or extract_title(md_text) or Path(source).stem
    if not slug:
        slug = slugify(title)

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESEARCH_DIR / f"{slug}.md"

    header = build_header(title, source, method, quality,
                          source_url_override=youtube_url or pdf_url,
                          cleaned_with=cleaned_with)
    out_path.write_text(header + "\n\n" + md_text, encoding="utf-8")
    print(f"Saved: {out_path}", file=sys.stderr)

    if quality["verdict"] == "bad":
        print(
            f"\nWARNING: Quality verdict is BAD (score={quality['score']}). "
            "The ingest-paper skill can guide you through fallback options.",
            file=sys.stderr,
        )
        sys.exit(2)
    elif quality["verdict"] == "marginal":
        print(
            f"\nNOTE: Quality verdict is MARGINAL (score={quality['score']}). "
            "Output saved but may be garbled. Consider trying a different method.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()

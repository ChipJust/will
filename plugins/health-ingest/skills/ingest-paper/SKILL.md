---
name: ingest-paper
description: This skill should be used when the user wants to save a research paper, article, or video transcript for future reference — e.g. "ingest this paper", "save this to research", "add this transcript", provides a PDF/DOCX/VTT/URL and asks to archive it, or is referencing a source that should be preserved in the health research library.
version: 1.0.0
---

# Skill: Ingest Research Paper or Transcript

Save a parsable, citable copy of any source used in health decisions into `research/` as versioned markdown.

## Entry Point

```
uv run python tools/ingest.py <source> [--slug SLUG] [--title TITLE] [--force-method METHOD]
```

- `<source>`: path to PDF, DOCX, VTT, HTML file, or a URL
- Default method is chosen by file type; use `--force-method` when directing a fallback
- Exit code 2 = bad quality; exit code 1 = extractor failed

---

## Step 1 — Identify the Source Format

| Extension / Type | Default method |
|------------------|---------------|
| `.pdf` | `pymupdf` |
| `.docx` / `.doc` | `docx` |
| `.vtt` | `vtt` |
| `.html` / `.htm` / URL | `html` |

For VTT files, skip quality checking — transcript text is always clean. Go straight to done.

---

## Step 2 — Run the Default Extraction

```
uv run python tools/ingest.py <source>
```

Read the quality output printed to stderr:
- `verdict=ok` → done
- `verdict=marginal` → done, but note the quality score in your response
- `verdict=bad` → proceed to fallback chain

### Cleanup pass (auto)

`ingest.py` runs the extracted markdown through `tools/extract/clean_md.py`
before quality scoring. Profiles are auto-detected by signature regex; when one
activates, you'll see:

```
Cleaned: profile=gmail-print removed: timestamp=18, page_url=18, ...
```

and the saved YAML frontmatter gains `cleaned_with: <profile>`. No action
needed — but **after a successful ingest, eyeball the output once.** If the
saved markdown still has repeating headers/footers (per-page timestamps, page
numbers, email envelope lines, etc.) and *no* `cleaned_with` line is present,
the source format is new.

**Extend, don't hand-edit.** Add a new profile to the `PROFILES` dict in
`tools/extract/clean_md.py`:
- `signature`: a regex unique to that source family (raises detection)
- `signature_threshold`: how many matches before activating (usually 2–3)
- `line_patterns`: dict of `{name: regex}`, one regex per type of noise line
- `description`: human-readable summary

Re-run ingest with `--slug <same-slug>` to overwrite. Inspect `cleaned_with`
in the new frontmatter and the stderr removal counts. Commit the new profile
together with the cleaned `.md`.

To preview without re-extracting:
```
uv run python tools/extract/clean_md.py research/refs/<slug>.md --profile <name>
```
or `--list-profiles` to see what's known.

---

## Step 3 — Fallback Chain (PDF bad quality only)

Work through these in order. Stop as soon as verdict is `ok` or `marginal`.

### 3a. Try pdfminer (different PDF engine)

```
uv run python tools/ingest.py <pdf> --force-method pdfminer
```

### 3b. Look for a DOCX in the same directory

Check the directory containing the PDF for any `.docx` or `.doc` file with a similar name.

```
uv run python tools/ingest.py <found.docx> --slug <same-slug-as-pdf>
```

### 3c. Look for a local HTML file

Check the same directory for `.html` or `.htm` files.

### 3d. Try to find an online HTML version

See `references/format-detection.md` for where to look by source type (DOI, PubMed, arXiv, etc.).

```
uv run python tools/ingest.py <url> --slug <slug>
```

### 3e. Marker placeholder

If all methods above fail or produce bad quality, tell the user:

> "Extraction quality is too low for all available methods. The `marker` library (ML-based, ~500MB) would likely succeed on this document. To enable it:
> 1. Add `marker-pdf` to `pyproject.toml` dependencies, then `uv sync`
> 2. Create `tools/extract/from_marker.py` following the same interface as the other extractors (one arg: pdf path, markdown to stdout)
> 3. Re-run with `--force-method marker`"

---

## Step 4 — After Successful Ingestion

1. Confirm the saved path to the user (`research/<slug>.md`)
2. Note the method used and quality score
3. If the source had a DOI or URL, verify it's in the YAML header — if not, add it with a manual edit

---

## Source Header Format

Every ingested file starts with YAML frontmatter. Verify it looks like:

```yaml
---
title: "Full Article Title"
source_file: original-filename.pdf     # if from local file
source_url: https://doi.org/...        # if URL known
ingest_date: 2026-04-05
ingest_method: pymupdf
quality_score: 87
---
```

If `source_url` is missing and you know the DOI or URL, add it manually.

---

## Quality Score Reference

See `references/quality-thresholds.md` for full detail.

| Verdict | Score | Action |
|---------|-------|--------|
| ok | ≥ 75 | Done |
| marginal | 50–74 | Done; note it |
| bad | < 50 | Fallback chain |

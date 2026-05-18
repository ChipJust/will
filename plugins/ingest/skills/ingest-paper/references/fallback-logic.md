# Fallback Decision Tree

Full decision logic for the ingest-paper skill.

```
Input received
│
├── VTT file
│   └── from_vtt.py → save → DONE (no quality check needed)
│
├── DOCX/DOC file
│   └── from_docx.py → quality check
│       ├── ok/marginal → DONE
│       └── bad → very unusual; likely corrupt file → tell user
│
├── URL
│   └── from_html.py → quality check
│       ├── ok/marginal → DONE
│       └── bad → JS-rendered page? Ask user to save HTML locally and retry
│
└── PDF
    ├── from_pymupdf.py → quality check
    │   ├── ok/marginal → DONE
    │   └── bad ──────────────────────────────────────────┐
    │                                                      ▼
    ├── from_pdfminer.py → quality check                  │
    │   ├── ok/marginal → DONE                            │
    │   └── bad ──────────────────────────────────────────┤
    │                                                      ▼
    ├── Look for DOCX in same dir                         │
    │   ├── found → from_docx.py → quality check         │
    │   │   ├── ok/marginal → DONE                       │
    │   │   └── bad → continue                           │
    │   └── not found → continue ────────────────────────┤
    │                                                      ▼
    ├── Look for HTML in same dir                         │
    │   ├── found → from_html.py → quality check         │
    │   │   ├── ok/marginal → DONE                       │
    │   │   └── bad → continue                           │
    │   └── not found → continue ────────────────────────┤
    │                                                      ▼
    ├── Try DOI → HTML                                    │
    │   ├── DOI found in PDF metadata or text            │
    │   │   └── from_html.py → quality check             │
    │   │       ├── ok/marginal → DONE                   │
    │   │       └── bad → continue                       │
    │   └── no DOI → continue ──────────────────────────┤
    │                                                      ▼
    ├── Try PubMed/PMC → HTML (biomedical papers)        │
    │   └── search by title → from_html.py               │
    │       ├── ok/marginal → DONE                       │
    │       └── bad → continue ─────────────────────────┤
    │                                                      ▼
    ├── Try arXiv/bioRxiv → HTML (preprints)             │
    │   └── search by title → from_html.py               │
    │       ├── ok/marginal → DONE                       │
    │       └── bad → continue ─────────────────────────┤
    │                                                      ▼
    └── MARKER PLACEHOLDER                               │
        Tell user:                                       │
        - What failed and why (quality scores)          ◄┘
        - How to enable marker-pdf
        - Manual copy-paste as last resort
```

## When to Stop Early

- If `word_count < 50` on the PDF: it's almost certainly image-only or DRM-locked.
  Skip pdfminer and go straight to alternate format search.

- If the paper is from a known open-access source (PMC, arXiv, bioRxiv),
  jump to that step before trying pdfminer — HTML will be cleaner anyway.

## Slug Consistency Across Retries

When retrying with a different source format, always pass `--slug <same-slug>` so
the output file is overwritten rather than creating a duplicate.

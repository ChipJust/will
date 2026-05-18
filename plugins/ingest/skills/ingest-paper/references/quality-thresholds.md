# Quality Thresholds Reference

`tools/extract/quality.py` outputs a JSON object with these fields and a composite score.

## Metrics

| Metric | What it measures | Bad | Marginal | OK |
|--------|-----------------|-----|----------|----|
| `word_count` | Total words extracted | < 100 | 100–400 | > 400 |
| `valid_word_ratio` | Fraction of tokens that look like real words (2–20 chars, ≥60% alpha) | < 0.70 | 0.70–0.82 | > 0.82 |
| `median_line_length` | Median length of non-empty lines in chars | < 25 | 25–40 | > 40 |
| `noise_ratio` | Fraction of chars that are non-ASCII or control characters | > 0.08 | 0.04–0.08 | < 0.04 |

## Weights

```
score = 0.15 × word_count_score
      + 0.40 × valid_word_ratio_score
      + 0.25 × median_line_length_score
      + 0.20 × noise_ratio_score
```

`valid_word_ratio` carries the most weight because garbled two-column interleaving
primarily shows up as nonsense tokens, not short lines or noise chars.

## Interpreting Common Failure Patterns

**Low `valid_word_ratio` + short `median_line_length`**
→ Two-column interleaving. pymupdf reads left column top-to-bottom then right column,
  producing single words per line. Try pdfminer or look for DOCX/HTML version.

**High `noise_ratio`**
→ Encoding issue or scanned/OCR'd PDF. pdfminer may handle encoding differently;
  otherwise HTML version is best bet.

**Low `word_count`**
→ Extraction nearly failed (image-only PDF, DRM, or corrupt file). Look for alternate
  format — nothing else will help.

**`marginal` verdict**
→ Usable but imperfect. Note quality score in research file header (already automatic).
  Do not trigger fallback unless the text looks visibly garbled when you read it.

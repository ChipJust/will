# Finding Alternate Source Formats

When a PDF extraction fails, try these sources in order.

## 1. Same Directory as the PDF

Look for files with the same stem or similar name:
- `*.docx`, `*.doc` — journal Word source, cleanest possible input
- `*.html`, `*.htm` — saved web page

## 2. DOI → HTML

If the PDF contains a DOI (usually on the first page or in the header/footer),
fetch the HTML version:

```
uv run python tools/ingest.py https://doi.org/<DOI> --slug <slug>
```

Most journals serve a readable HTML view at the DOI URL.

## 3. PubMed / PMC

For biomedical papers, search by title or PMID:
- PubMed abstract: `https://pubmed.ncbi.nlm.nih.gov/<PMID>/`
- PMC full text (free): `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC<ID>/`

PMC full text is preferable — it includes the full body, not just abstract.

## 4. arXiv

For preprints, the HTML abstract page often links to an HTML version:
- `https://arxiv.org/abs/<ID>` — abstract
- `https://arxiv.org/html/<ID>` — full HTML (available for newer papers)

## 5. bioRxiv / medRxiv

Similar to arXiv:
- `https://www.biorxiv.org/content/<DOI>` → look for "Full Text" link
- The HTML article view is usually at the same URL with `?view=full`

## 6. Semantic Scholar

Often has an open-access PDF or HTML link:
- `https://www.semanticscholar.org/paper/<title-search>`

## 7. Unpaywall / Open Access Button

If the paper is paywalled, these services find legal open-access copies:
- Unpaywall: `https://unpaywall.org/<DOI>`
- Tell the user to check these rather than attempting extraction yourself

## Notes

- Prefer HTML over PDF when both are available — trafilatura handles article HTML well
- If the journal HTML is heavily JavaScript-rendered and trafilatura gets < 200 words,
  try saving the page locally first (Ctrl+S in browser) and passing the `.html` file

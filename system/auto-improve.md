# Auto-Improve Pattern

Tools that process external data should evaluate whether they need updating
and surface candidates — never auto-apply changes.

## The rule

Each tool run checks its own assumptions against the data it just processed.
When it finds a mismatch (new format, unknown identifier, degraded output),
it surfaces the discrepancy as an improvement candidate on stderr or in a
structured report. The human or agent decides whether to act.

## Instances

1. **Papers — clean_md profiles (2026-05-17).** `tools/extract/clean_md.py` has
   a `profiles` dict keyed by signature regex. When a new publisher's boilerplate
   isn't matched, quality scores drop and the tool logs "no profile matched."
   The agent can then inspect the raw output and propose a new profile entry.

2. **Positions — ingest_positions.py parser fix (2026-04-28).** The position
   parser surfaced a candidate when a brokerage changed its CSV column names.
   The mismatch was logged, not silently dropped — the agent fixed the parser
   in the same session.

3. **Prices — CUSIP override candidates from prices.py (2026-04-28).** On first
   run, `prices.py` logged tickers whose CUSIP lookup failed, with enough context
   to build override entries. The overrides were proposed as a batch, not
   auto-inserted.

## When to apply

Any tool that:
- Parses external formats that may change (CSVs, HTML, PDFs)
- Maps identifiers that may be incomplete (tickers, CUSIPs, profiles)
- Produces quality scores that may degrade

should log improvement candidates rather than failing silently or auto-fixing.
The output should include enough context for a human or agent to act:
what was expected, what was found, and what a fix would look like.

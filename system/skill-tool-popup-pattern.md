# Skill-Tool Popup Pattern

When an agent-level workflow requires pre-steps before a tool call, those
pre-steps should move INSIDE the tool, not stay in the skill docs or agent
instructions. Each manual pre-step is a permission popup when the agent runs
it via Bash — and popups multiply per batch item.

## The rule

If a skill's instructions say "before calling the tool, do X" and X is
deterministic, bake X into the tool. The skill should invoke the tool with
the raw input and let the tool handle routing.

## Instances

1. **clean_md graduation into ingest.py (2026-05-17).** `ingest-paper` SKILL.md
   described a separate `clean_md.py` call between extract and quality. Neither
   per-repo `ingest.py` actually called it. Unified `will/tools/ingest.py` runs
   clean_md internally — one tool call, no extra popup.

2. **YouTube `yt-dlp --get-title` baked into ingest.py (2026-05-24).** The skill
   instructed the agent to run `yt-dlp --get-title` before calling ingest. For a
   10-video batch, that was 10 extra Bash popups (plus 10 more for the ingest
   calls). Now `ingest.py` detects YouTube URLs and fetches the title itself.
   Retired 6 popups per batch item.

3. **PDF URL detection baked into ingest.py (2026-06-13).** `ingest.py` defaulted
   to the HTML extractor for all URL inputs, regardless of extension. PDF URLs
   failed with "No article content extracted" until you manually `curl`-downloaded
   the file and passed the local path. Now `ingest.py` detects `.pdf` in the URL
   path, downloads to a temp file, and routes to pymupdf. Retired 4 fallback
   steps per PDF URL.

## When to apply

Any time you see a skill's instructions describing a deterministic pre-step
or post-step around a tool invocation, that step is a candidate for moving
into the tool. Signs:

- The pre-step always runs (no judgment call)
- It generates input for the tool (download, convert, detect format)
- Skipping it causes a predictable failure mode
- It multiplies across batch items

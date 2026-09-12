"""Extract a research agent's final report from its transcript into markdown.

Why this exists: subagent reports arrive in the orchestrator's context, get
summarized, and the primary research — citations, URLs, evidence grading — is
lost when the session ends. The transcripts hold the full report, but they are
far too large to read into context. This tool pulls the final text block out of
the JSONL and writes it to the repo's `research/agent-reports/`, where
`research_index.py` picks it up. Zero context cost to the orchestrator.

Two transcript layouts exist and both are searched, newest first:
  1. ~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl  (current)
  2. %LOCALAPPDATA%/Temp/claude/*/*/tasks/<id>.output                   (older)
Records look like:
  {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}, ...}
The agent's return value is the LAST assistant record whose content holds a
text block. Records ending in tool_use mean the agent is still working.

An agent killed mid-run (session ended, cancelled, sibling failure) has NO
final text and so nothing to harvest — but its fetched pages are still on
disk and are the expensive part. `--dump` writes that raw material out for
synthesis by hand instead of re-running the research.

Input:  --list, or --agent <id> plus metadata flags, or --agent <id> --dump
Output: writes <repo>/research/agent-reports/<date>-<slug>.md; prints the path.
        With --dump: writes a plain-text salvage file and prints its path.

Sample:
    $ uv run python tools/harvest_agent_report.py --list
    a1e8fb79275757e8b   98.2 KB  DONE     Research NAD precursor supplementation for a specific...
    ac3eaaca2fad537be    1.0 MB  RUNNING  Research the health implications of daily swimming...

    $ uv run python tools/harvest_agent_report.py --agent a1e8fb79275757e8b \
        --repo health --slug nad-precursor --title "NAD Precursor Introduction" \
        --question "Which NAD precursor, at what dose?" --topics nad,nr,nmn,tmg
    Wrote D:/_code/health/research/agent-reports/2026-08-22-nad-precursor.md (4812 words)

    $ uv run python tools/harvest_agent_report.py --agent ac9802d8bb49a98cf --dump
    Wrote C:/Users/chipj/AppData/Local/Temp/agent-ac9802d8bb49a98cf-salvage.txt (116.0 KB)
    Agent has no final report (killed or still running); 43 tool results dumped.
    Read it in slices and write the report yourself into <repo>/research/agent-reports/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

TASKS_ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "claude"
PROJECTS_ROOT = Path.home() / ".claude" / "projects"
CODE_ROOT = Path("D:/_code")


def looks_like_transcript(path: Path) -> bool:
    """True if the file is agent JSONL and not a persisted tool output.

    tasks/ holds both: `<agent-id>.output` transcripts and `<slug>.output`
    dumps of oversized tool results, which are plain text.
    """
    try:
        with io.open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                return isinstance(record, dict) and ("type" in record or "message" in record)
    except (json.JSONDecodeError, OSError):
        return False
    return False


def find_transcripts() -> list[Path]:
    """Every agent transcript on disk, newest first, across both layouts.

    One agent can appear in both layouts; the larger file wins, since a
    truncated copy would silently lose fetched pages.
    """
    found: list[Path] = []
    if PROJECTS_ROOT.is_dir():
        found += PROJECTS_ROOT.glob("*/*/subagents/agent-*.jsonl")
    if TASKS_ROOT.is_dir():
        found += TASKS_ROOT.glob("*/*/tasks/*.output")
    best: dict[str, Path] = {}
    for path in found:
        if not path.is_file() or path.stat().st_size == 0:
            continue
        if not looks_like_transcript(path):
            continue
        agent = agent_id_of(path)
        if agent not in best or path.stat().st_size > best[agent].stat().st_size:
            best[agent] = path
    return sorted(best.values(), key=lambda p: p.stat().st_mtime, reverse=True)


def agent_id_of(path: Path) -> str:
    """The bare agent id, whichever layout the file came from."""
    stem = path.stem
    return stem[len("agent-") :] if stem.startswith("agent-") else stem


def transcript_path(agent_id: str) -> Path | None:
    # Accept the id with or without the "agent-" prefix the filenames carry.
    wanted = agent_id[len("agent-") :] if agent_id.startswith("agent-") else agent_id
    for path in find_transcripts():
        if agent_id_of(path) == wanted:
            return path
    return None


def describe(path: Path) -> str:
    """The agent's task description from its sidecar meta file, if present."""
    meta = path.with_suffix(".meta.json")
    if not meta.is_file():
        return ""
    try:
        data = json.loads(meta.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return ""
    return str(data.get("description", "")) if isinstance(data, dict) else ""


def read_records(path: Path):
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Transcripts contain bare scalars on some lines; skip non-objects.
            if isinstance(record, dict):
                yield record


def extract_report(path: Path) -> tuple[str, str]:
    """Return (final_text, first_prompt). Empty final_text means no report.

    The report is the text of the FINAL assistant turn, and only that. An
    assistant turn that also issues tool calls is not a final turn — it is
    interim narration ("let me check X next"). Harvesting such a line, which
    an earlier version did whenever it was the last text block seen anywhere,
    writes a plausible-looking report file containing none of the research.
    A killed or still-running agent therefore has no report by definition.
    """
    first_prompt = ""
    final_text = ""
    for record in read_records(path):
        content = record.get("message", {}).get("content")
        if isinstance(content, str):
            if record.get("type") == "user" and not first_prompt:
                first_prompt = content
            continue
        if not isinstance(content, list):
            continue
        blocks = [b for b in content if isinstance(b, dict)]
        texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        if record.get("type") != "assistant":
            if not first_prompt and texts:
                first_prompt = texts[0]
            continue
        still_working = any(b.get("type") == "tool_use" for b in blocks)
        final_text = "" if still_working else "\n\n".join(t for t in texts if t.strip())
    return final_text, first_prompt


def dump_transcript(path: Path, out_path: Path) -> int:
    """Write every tool result and agent text block to out_path. Returns count.

    The point is recovery, not synthesis: a killed agent's fetched pages are
    the expensive artifact, and no script can write the report from them.
    """
    calls: dict[str, tuple[str, dict]] = {}
    for record in read_records(path):
        content = record.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls[block.get("id", "")] = (
                    block.get("name", "?"),
                    block.get("input") or {},
                )

    results = 0
    with io.open(out_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(f"# Salvage dump of {path.as_posix()}\n")
        handle.write(f"# agent {agent_id_of(path)} — {describe(path) or 'no description'}\n")
        for record in read_records(path):
            content = record.get("message", {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and record.get("type") == "assistant":
                    handle.write(f"\n##### AGENT SAID\n{block.get('text', '')}\n")
                elif block.get("type") == "tool_result":
                    name, params = calls.get(block.get("tool_use_id", ""), ("?", {}))
                    label = params.get("url") or params.get("query") or ""
                    body = block.get("content")
                    if not isinstance(body, str):
                        body = json.dumps(body, ensure_ascii=False)
                    handle.write(f"\n===== {name} :: {label}\n{body}\n")
                    results += 1
    return results


def cmd_list() -> int:
    rows = []
    for path in find_transcripts():
        size = path.stat().st_size
        if size == 0:
            continue
        final, prompt = extract_report(path)
        label = describe(path) or prompt
        rows.append((agent_id_of(path), size, bool(final), " ".join(label.split())[:70]))
    if not rows:
        print("No non-empty agent transcripts found.")
        print(f"Looked in {PROJECTS_ROOT.as_posix()} and {TASKS_ROOT.as_posix()}", file=sys.stderr)
        return 1
    rows.sort(key=lambda r: -r[1])
    for agent_id, size, done, prompt in rows:
        human = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / 1048576:.1f} MB"
        print(f"{agent_id}  {human:>10}  {'DONE   ' if done else 'NO REPORT'}  {prompt}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--list", action="store_true", help="list transcripts and exit")
    parser.add_argument("--agent", help="agent id to harvest")
    parser.add_argument(
        "--dump",
        action="store_true",
        help="write the agent's raw tool results to a file for hand synthesis "
        "(use when the agent was killed before writing a report)",
    )
    parser.add_argument("--out", type=Path, help="destination for --dump")
    parser.add_argument("--repo", default="health", help="target repo name under D:/_code")
    parser.add_argument("--slug", help="filename slug (kebab-case)")
    parser.add_argument("--title", help="report title")
    parser.add_argument("--question", default="", help="the question the agent answered")
    parser.add_argument("--topics", default="", help="comma-separated topic keywords")
    parser.add_argument("--findings", default="", help="one-line key finding summary")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    args = parser.parse_args()

    if args.list:
        return cmd_list()

    if args.dump:
        if not args.agent:
            print("error: --dump requires --agent", file=sys.stderr)
            return 2
    elif not (args.agent and args.slug and args.title):
        print("error: --agent, --slug and --title are required", file=sys.stderr)
        return 2

    path = transcript_path(args.agent)
    if path is None:
        print(f"error: no transcript for agent {args.agent}", file=sys.stderr)
        print("       run --list to see the ids that are on disk", file=sys.stderr)
        return 2

    report, prompt = extract_report(path)

    if args.dump:
        out_path = args.out or Path(tempfile.gettempdir()) / f"agent-{agent_id_of(path)}-salvage.txt"
        results = dump_transcript(path, out_path)
        size = out_path.stat().st_size
        print(f"Wrote {out_path.as_posix()} ({size / 1024:.1f} KB)")
        if report:
            print(f"Note: this agent DID finish — harvest it directly instead of synthesizing.")
        else:
            print(f"Agent has no final report (killed or still running); {results} tool results dumped.")
        print("Read it in slices and write the report yourself into <repo>/research/agent-reports/.")
        return 0

    if not report:
        print(f"error: agent {args.agent} has no final text (killed, or still running)", file=sys.stderr)
        print(f"       its fetched pages are still recoverable:", file=sys.stderr)
        print(f"       --agent {args.agent} --dump", file=sys.stderr)
        return 1

    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    out_dir = CODE_ROOT / args.repo / "research" / "agent-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.date}-{args.slug}.md"

    front = [
        "---",
        f'title: "{args.title}"',
        "type: agent-report",
        f"date: {args.date}",
        f"repo: {args.repo}",
        f"agent_id: {args.agent}",
    ]
    if args.question:
        front.append(f'question: "{args.question}"')
    if args.findings:
        front.append(f'key_findings: "{args.findings}"')
    if topics:
        front.append(f"topics: [{', '.join(topics)}]")
    front += ["---", ""]

    with io.open(out_path, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(front))
        handle.write(report.strip() + "\n")

    print(f"Wrote {out_path.as_posix()} ({len(report.split())} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

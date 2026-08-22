"""Extract a research agent's final report from its transcript into markdown.

Why this exists: subagent reports arrive in the orchestrator's context, get
summarized, and the primary research — citations, URLs, evidence grading — is
lost when the session ends. The transcripts hold the full report, but they are
far too large to read into context. This tool pulls the final text block out of
the JSONL and writes it to the repo's `research/agent-reports/`, where
`research_index.py` picks it up. Zero context cost to the orchestrator.

Transcript layout (Claude Code task output, JSONL):
  {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}, ...}
The agent's return value is the LAST assistant record whose content holds a
text block. Records ending in tool_use mean the agent is still working.

Input:  --list, or --agent <id> plus metadata flags
Output: writes <repo>/research/agent-reports/<date>-<slug>.md; prints the path

Sample:
    $ uv run python tools/harvest_agent_report.py --list
    a1e8fb79275757e8b   98.2 KB  DONE     Research NAD precursor supplementation for a specific...
    ac3eaaca2fad537be    1.0 MB  RUNNING  Research the health implications of daily swimming...

    $ uv run python tools/harvest_agent_report.py --agent a1e8fb79275757e8b \
        --repo health --slug nad-precursor --title "NAD Precursor Introduction" \
        --question "Which NAD precursor, at what dose?" --topics nad,nr,nmn,tmg
    Wrote D:/_code/health/research/agent-reports/2026-08-22-nad-precursor.md (4812 words)
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TASKS_ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "claude"
CODE_ROOT = Path("D:/_code")


def find_task_dirs() -> list[Path]:
    """All task directories under the Claude Code temp tree, newest first."""
    if not TASKS_ROOT.is_dir():
        return []
    dirs = [p for p in TASKS_ROOT.glob("*/*/tasks") if p.is_dir()]
    return sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)


def transcript_path(agent_id: str) -> Path | None:
    for tasks in find_task_dirs():
        candidate = tasks / f"{agent_id}.output"
        if candidate.is_file():
            return candidate
    return None


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
    """Return (final_text, first_prompt). Empty final_text means still running."""
    final_text = ""
    first_prompt = ""
    for record in read_records(path):
        content = record.get("message", {}).get("content")
        if not isinstance(content, list):
            if isinstance(content, str) and record.get("type") == "user" and not first_prompt:
                first_prompt = content
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            text = block.get("text", "")
            if record.get("type") == "assistant":
                # Keep overwriting: the last one wins.
                final_text = text
            elif not first_prompt:
                first_prompt = text
    return final_text, first_prompt


def cmd_list() -> int:
    rows = []
    for tasks in find_task_dirs():
        for out in tasks.glob("*.output"):
            size = out.stat().st_size
            if size == 0:
                continue
            final, prompt = extract_report(out)
            rows.append((out.stem, size, bool(final), " ".join(prompt.split())[:70]))
    if not rows:
        print("No non-empty agent transcripts found.")
        return 1
    rows.sort(key=lambda r: -r[1])
    for agent_id, size, done, prompt in rows:
        human = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / 1048576:.1f} MB"
        print(f"{agent_id}  {human:>10}  {'DONE   ' if done else 'RUNNING'}  {prompt}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--list", action="store_true", help="list transcripts and exit")
    parser.add_argument("--agent", help="agent id to harvest")
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

    if not (args.agent and args.slug and args.title):
        print("error: --agent, --slug and --title are required", file=sys.stderr)
        return 2

    path = transcript_path(args.agent)
    if path is None:
        print(f"error: no transcript for agent {args.agent}", file=sys.stderr)
        return 2

    report, prompt = extract_report(path)
    if not report:
        print(f"error: agent {args.agent} has no final text yet (still running?)", file=sys.stderr)
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

#!/usr/bin/env python3
"""
wake_report.py — Generate a session briefing from HANDOFF context layers.

Called automatically by the SessionStart hook, or manually via /wake.
Scans all agentic repos under D:/_code, extracts structured data from each
HANDOFF.md, and outputs a formatted markdown briefing.

Usage
    # Hook mode (stdin JSON from Claude Code, stdout injected as system reminder)
    python D:/_code/will/tools/wake_report.py

    # Manual mode (raw markdown to stdout)
    python D:/_code/will/tools/wake_report.py --raw

Input (hook mode)
    JSON on stdin with session context — same schema as statusline.py:
    {"cwd": "D:\\_code\\home", "workspace": {"project_dir": "D:\\_code\\home"}, ...}

    Falls back to CLAUDE_PROJECT_DIR env var, then os.getcwd().

Output
    Formatted markdown briefing to stdout.
    Cache written to D:/_code/will/.cache/wake-report.md.
    Debug log at ~/.claude/wake-report-debug.log.
"""

import io
import json
import os
import re
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

CODE_ROOT = Path("D:/_code")
WILL_DIR = CODE_ROOT / "will"
CACHE_DIR = WILL_DIR / ".cache"
CACHE_FILE = CACHE_DIR / "wake-report.md"
LOG_FILE = Path.home() / ".claude" / "wake-report-debug.log"

SUBJECT_REPOS = ["health", "money", "home", "writing", "vibedaw"]

RE_DATE = re.compile(r"\*Last updated:\s*(\d{4}-\d{2}-\d{2})")
RE_THINKING_HEADING = re.compile(
    r"^#{2,3}\s+.*[Tt]hinking\s+[Ff]rame", re.IGNORECASE
)
RE_THINKING_INLINE = re.compile(r"^\*\*[Tt]hinking\s+[Ff]rame:\*\*\s*(.+)")
RE_AGENT_CATEGORY = re.compile(r"[Aa]gent\s+can\s+(?:start|do)")
RE_CHIP_CATEGORY = re.compile(r"[Nn]eeds\s+[Cc]hip")
RE_UNCHECKED = re.compile(r"^- \[ \]\s+(.+)")
RE_CHECKED = re.compile(r"^- \[x\]\s+")
RE_HEADING = re.compile(r"^(#{1,4})\s+(.+)")
RE_BOLD_TOPIC = re.compile(r"^\*\*([^*]+):\*\*\s*(.+)")
RE_OPEN_ITEMS_HEADING = re.compile(
    r"(?:[Oo]pen\s+(?:next\s+steps|system.level\s+items))|(?:[Pp]ersonal\s+open\s+items)"
)
RE_CROSS_CUTTING_HEADING = re.compile(r"[Cc]ross.cutting\s+concerns")


def log(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass


def resolve_cwd():
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except Exception:
        pass

    if raw.strip():
        log(f"stdin: {raw[:500]}")
        try:
            data = json.loads(raw)
            cwd = data.get("cwd") or ""
            if not cwd:
                ws = data.get("workspace", {})
                cwd = ws.get("project_dir") or ws.get("current_dir") or ""
            if cwd:
                return Path(cwd)
        except (json.JSONDecodeError, AttributeError):
            log(f"stdin JSON parse failed, falling back")

    env = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env:
        return Path(env)

    return Path(os.getcwd())


def identify_repo(cwd):
    try:
        rel = cwd.relative_to(CODE_ROOT)
        repo_name = str(rel).replace("\\", "/").split("/")[0]
        repo_path = CODE_ROOT / repo_name
        if repo_path.is_dir():
            return repo_name, repo_path
    except (ValueError, IndexError):
        pass
    return None, None


def parse_handoff(repo_name, repo_path=None):
    if repo_path is None:
        repo_path = CODE_ROOT / repo_name
    handoff = repo_path / "HANDOFF.md"

    result = {
        "repo": repo_name,
        "path": handoff,
        "exists": False,
        "last_updated": None,
        "staleness_days": None,
        "thinking_frame": None,
        "agent_items": [],
        "chip_items": [],
        "uncategorized_items": [],
        "completed_count": 0,
        "cross_cutting": [],
        "personal_items": [],
    }

    if not handoff.exists():
        return result

    try:
        text = handoff.read_text(encoding="utf-8")
    except Exception as e:
        log(f"Failed to read {handoff}: {e}")
        return result

    result["exists"] = True
    lines = text.splitlines()

    # --- Extract date from first 5 lines ---
    for line in lines[:5]:
        m = RE_DATE.search(line)
        if m:
            result["last_updated"] = m.group(1)
            try:
                updated = date.fromisoformat(m.group(1))
                result["staleness_days"] = (date.today() - updated).days
            except ValueError:
                pass
            break

    # --- State machine for section parsing ---
    item_category = "uncategorized"  # agent / chip / uncategorized
    thinking_lines = []
    in_thinking = False
    in_cross_cutting = False
    in_open_items = False
    in_cross_survey = False  # cross-repo survey section — skip item collection
    hit_blank_after_thinking = False

    for line in lines:
        stripped = line.strip()

        # Detect headings
        hm = RE_HEADING.match(stripped)
        if hm:
            level = len(hm.group(1))
            heading_text = hm.group(2)

            if level <= 2:
                in_thinking = False
                in_cross_cutting = False
                in_open_items = False
                in_cross_survey = False
                item_category = "uncategorized"

            # Cross-repo survey (will only) — skip item collection in this section
            if re.search(r"[Cc]ross.repo\s+survey", heading_text):
                in_cross_survey = True
                in_thinking = False
                in_cross_cutting = False
                in_open_items = False
                continue

            # Thinking frame heading
            if RE_THINKING_HEADING.match(stripped):
                in_thinking = True
                in_cross_cutting = False
                in_open_items = False
                continue

            # Cross-cutting concerns heading
            if RE_CROSS_CUTTING_HEADING.search(heading_text):
                in_cross_cutting = True
                in_thinking = False
                in_open_items = False
                continue

            # Open items heading (only outside cross-repo survey)
            if not in_cross_survey and RE_OPEN_ITEMS_HEADING.search(heading_text):
                in_open_items = True
                in_thinking = False
                in_cross_cutting = False
                item_category = "uncategorized"
                continue

            # Agent/Chip sub-headings (only outside cross-repo survey)
            if not in_cross_survey and RE_AGENT_CATEGORY.search(heading_text):
                item_category = "agent"
                in_open_items = True
                continue
            if not in_cross_survey and RE_CHIP_CATEGORY.search(heading_text):
                item_category = "chip"
                in_open_items = True
                continue

        # Skip item collection inside cross-repo survey
        if in_cross_survey:
            continue

        is_checkbox = RE_UNCHECKED.match(stripped) or RE_CHECKED.match(stripped)

        # Non-heading agent/chip labels (health style: plain text "Agent can start immediately:")
        # Only on non-checkbox lines to avoid "needs Chip" inside item text flipping category
        if not hm and not is_checkbox and in_open_items:
            if RE_AGENT_CATEGORY.search(stripped):
                item_category = "agent"
                continue
            if RE_CHIP_CATEGORY.search(stripped):
                item_category = "chip"
                continue

        # Also detect agent/chip labels even before an open-items heading
        # (health uses bold labels without a ## heading)
        if not hm and not is_checkbox and not in_open_items:
            if RE_AGENT_CATEGORY.search(stripped) and ":" in stripped:
                in_open_items = True
                item_category = "agent"
                continue
            if RE_CHIP_CATEGORY.search(stripped) and ":" in stripped:
                in_open_items = True
                item_category = "chip"
                continue

        # Inline thinking frame (health style)
        if not result["thinking_frame"]:
            tm = RE_THINKING_INLINE.match(stripped)
            if tm:
                result["thinking_frame"] = tm.group(1).strip()
                continue

        # Collect thinking frame lines
        if in_thinking and not result["thinking_frame"]:
            if stripped == "":
                if thinking_lines:
                    hit_blank_after_thinking = True
            elif hit_blank_after_thinking:
                # Second paragraph — stop collecting
                in_thinking = False
                result["thinking_frame"] = " ".join(thinking_lines).strip()
            elif stripped.startswith("---"):
                if thinking_lines:
                    in_thinking = False
                    result["thinking_frame"] = " ".join(thinking_lines).strip()
            else:
                thinking_lines.append(stripped)

        # Cross-cutting topic sentences
        if in_cross_cutting:
            bm = RE_BOLD_TOPIC.match(stripped)
            if bm:
                result["cross_cutting"].append(f"**{bm.group(1)}:** {bm.group(2)}")

        # Checkbox items
        um = RE_UNCHECKED.match(stripped)
        if um and in_open_items:
            item_text = um.group(1)
            if item_category == "agent":
                result["agent_items"].append(item_text)
            elif item_category == "chip":
                result["chip_items"].append(item_text)
            else:
                result["uncategorized_items"].append(item_text)
            continue

        if RE_CHECKED.match(stripped):
            result["completed_count"] += 1

    # Flush thinking frame if still collecting
    if in_thinking and thinking_lines and not result["thinking_frame"]:
        result["thinking_frame"] = " ".join(thinking_lines).strip()

    return result


def parse_personal_handoff():
    """Parse will-personal/HANDOFF.md for personal open items."""
    result = parse_handoff("will-personal")
    # Personal items are in the uncategorized bucket (no agent/chip split)
    personal = result["agent_items"] + result["chip_items"] + result["uncategorized_items"]
    result["personal_items"] = personal
    return result


def discover_repos():
    """Find all agentic repos and parse their HANDOFFs."""
    repos = {}

    # Parse system-tier repos
    repos["will"] = parse_handoff("will")
    repos["will-personal"] = parse_personal_handoff()

    # Parse known subject repos
    for name in SUBJECT_REPOS:
        repos[name] = parse_handoff(name)
        personal_name = f"{name}-personal"
        personal_path = CODE_ROOT / personal_name
        if personal_path.is_dir() and (personal_path / "HANDOFF.md").exists():
            repos[personal_name] = parse_handoff(personal_name, personal_path)

    # Dynamic scan for unknown repos with HANDOFF.md
    if CODE_ROOT.is_dir():
        for d in sorted(CODE_ROOT.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            if d.name in repos:
                continue
            if (d / "HANDOFF.md").exists():
                repos[d.name] = parse_handoff(d.name, d)
                log(f"Discovered unknown repo with HANDOFF: {d.name}")

    return repos


def format_staleness(days):
    if days is None:
        return ""
    if days == 0:
        return "today"
    return f"{days}d ago"


def build_report(repos, focus_repo, cwd):
    today = date.today().isoformat()
    lines = []

    # --- Header ---
    lines.append(f"## Session Brief -- {today}")
    if focus_repo and focus_repo in repos:
        lines.append(f"**Focus:** {focus_repo} (`{cwd}`)")
    elif focus_repo:
        lines.append(f"**Focus:** {focus_repo} (`{cwd}`)")
    else:
        lines.append(f"**Working in:** `{cwd}` (not an agentic repo)")
    lines.append("")

    # --- System Context ---
    will = repos.get("will", {})
    personal = repos.get("will-personal", {})

    lines.append("### System Context")

    will_date = will.get("last_updated", "unknown")
    will_stale = format_staleness(will.get("staleness_days"))
    lines.append(f"**Will frame** (updated {will_date}, {will_stale})")

    for item in will.get("cross_cutting", []):
        lines.append(f"- {item}")
    lines.append("")

    p_date = personal.get("last_updated", "unknown")
    p_stale = format_staleness(personal.get("staleness_days"))
    personal_items = personal.get("personal_items", [])
    if personal_items:
        lines.append(f"**Personal** (updated {p_date}, {p_stale})")
        for item in personal_items:
            lines.append(f"- [ ] {item}")
        lines.append("")

    # --- Ecosystem Overview ---
    lines.append("### Ecosystem Overview")
    lines.append("| Repo | Reflected | Agent-Ready | Needs Chip |")
    lines.append("|------|-----------|-------------|------------|")

    for name in SUBJECT_REPOS:
        repo = repos.get(name)
        if repo is None:
            continue

        if repo.get("exists"):
            reflected = repo["last_updated"] or "unknown"
            stale = format_staleness(repo.get("staleness_days"))
            if stale:
                reflected = f"{reflected} ({stale})"
        else:
            reflected = "no HANDOFF"

        agent_count = len(repo.get("agent_items", [])) + len(repo.get("uncategorized_items", []))
        chip_count = len(repo.get("chip_items", []))

        # Merge personal sibling counts
        personal_name = f"{name}-personal"
        p_repo = repos.get(personal_name)
        personal_note = ""
        if p_repo and p_repo.get("exists"):
            p_agent = len(p_repo.get("agent_items", [])) + len(p_repo.get("uncategorized_items", []))
            p_chip = len(p_repo.get("chip_items", []))
            if p_agent or p_chip:
                personal_note_parts = []
                if p_agent:
                    personal_note_parts.append(f"+{p_agent} personal")
                if p_chip:
                    personal_note_parts.append(f"+{p_chip} personal")
                # Add to display
                agent_str = str(agent_count)
                if p_agent:
                    agent_str = f"{agent_count} (+{p_agent} personal)"
                chip_str = str(chip_count)
                if p_chip:
                    chip_str = f"{chip_count} (+{p_chip} personal)"
            else:
                agent_str = str(agent_count) if repo.get("exists") else "--"
                chip_str = str(chip_count) if repo.get("exists") else "--"
        else:
            agent_str = str(agent_count) if repo.get("exists") else "--"
            chip_str = str(chip_count) if repo.get("exists") else "--"

        lines.append(f"| {name} | {reflected} | {agent_str} | {chip_str} |")

    # Dynamic repos not in SUBJECT_REPOS
    for name, repo in repos.items():
        if name in ["will", "will-personal"] or name in SUBJECT_REPOS:
            continue
        if name.endswith("-personal"):
            continue
        if not repo.get("exists"):
            continue
        reflected = repo.get("last_updated", "unknown")
        stale = format_staleness(repo.get("staleness_days"))
        if stale:
            reflected = f"{reflected} ({stale})"
        agent_count = len(repo.get("agent_items", [])) + len(repo.get("uncategorized_items", []))
        chip_count = len(repo.get("chip_items", []))
        lines.append(f"| {name} | {reflected} | {agent_count} | {chip_count} |")

    lines.append("")

    # --- Focus Repo Context ---
    if focus_repo and focus_repo != "will" and focus_repo in repos:
        repo = repos[focus_repo]
        if repo.get("exists"):
            lines.append(f"### {focus_repo} Context")

            if repo.get("thinking_frame"):
                lines.append(f"**Thinking frame:** {repo['thinking_frame']}")
                lines.append("")

            agent_items = repo.get("agent_items", []) + repo.get("uncategorized_items", [])
            chip_items = repo.get("chip_items", [])

            # Merge personal sibling items
            personal_name = f"{focus_repo}-personal"
            p_repo = repos.get(personal_name)
            if p_repo and p_repo.get("exists"):
                p_agent = p_repo.get("agent_items", []) + p_repo.get("uncategorized_items", [])
                p_chip = p_repo.get("chip_items", [])
                if p_agent:
                    agent_items = agent_items + [f"(personal) {i}" for i in p_agent]
                if p_chip:
                    chip_items = chip_items + [f"(personal) {i}" for i in p_chip]

            if agent_items:
                lines.append("**Agent can start:**")
                for item in agent_items:
                    lines.append(f"- [ ] {item}")
                lines.append("")

            if chip_items:
                lines.append("**Needs Chip:**")
                for item in chip_items:
                    lines.append(f"- [ ] {item}")
                lines.append("")

    elif focus_repo == "will":
        # Will is the focus — show system-level open items
        will_data = repos.get("will", {})
        all_items = (
            will_data.get("agent_items", [])
            + will_data.get("uncategorized_items", [])
        )
        chip_items = will_data.get("chip_items", [])

        if all_items or chip_items:
            lines.append("### will — Open System Items")
            if will_data.get("thinking_frame"):
                lines.append(f"**Thinking frame:** {will_data['thinking_frame']}")
                lines.append("")
            if all_items:
                lines.append("**Agent can start:**")
                for item in all_items:
                    lines.append(f"- [ ] {item}")
                lines.append("")
            if chip_items:
                lines.append("**Needs Chip:**")
                for item in chip_items:
                    lines.append(f"- [ ] {item}")
                lines.append("")

    # --- Closing ---
    lines.append("---")
    if focus_repo and focus_repo in repos and repos[focus_repo].get("exists"):
        lines.append(
            'Present this briefing. Ask: "Want to start there, or is there '
            'something else on your mind for this session?"'
        )
    else:
        lines.append(
            "Present this briefing. Ask what the user would like to work on."
        )

    return "\n".join(lines)


def write_cache(report):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(report, encoding="utf-8", newline="")
        log(f"Cache written to {CACHE_FILE}")
    except Exception as e:
        log(f"Cache write failed: {e}")


def main():
    log("=== wake_report.py START ===")
    start = datetime.now()

    raw_mode = "--raw" in sys.argv

    cwd = resolve_cwd()
    log(f"Resolved cwd: {cwd}")

    focus_repo, focus_path = identify_repo(cwd)
    log(f"Focus repo: {focus_repo}")

    repos = discover_repos()
    log(f"Discovered {len(repos)} repos: {list(repos.keys())}")

    report = build_report(repos, focus_repo, cwd)
    write_cache(report)

    elapsed = (datetime.now() - start).total_seconds()
    log(f"Report generated in {elapsed:.2f}s")

    print(report)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        log(f"FATAL ERROR:\n{tb}")
        print("Wake report failed. Run /wake manually.", file=sys.stderr)
        print("(wake report unavailable)")
        sys.exit(0)

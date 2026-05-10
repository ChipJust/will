#!/usr/bin/env python3
"""drive_migration_stage.py — Phase A: stage personal data from C: + F: to E:

Reads the action list from drive_migration_plan.PLAN and either previews it
(dry-run) or executes the copies. Originals on C: and F: are read-only
throughout — Phase A only writes to E:\\_migration\\.

Usage:
    # Dry run (default) — list every action with sizes; no writes
    uv run python projects/desktop-homelab/tools/drive_migration_stage.py

    # Actually copy
    uv run python projects/desktop-homelab/tools/drive_migration_stage.py --execute

    # Re-run completed actions (default behavior is to skip them)
    uv run python projects/desktop-homelab/tools/drive_migration_stage.py --execute --force

State is tracked in projects/desktop-homelab/tools/migration.state.json so
interrupted runs resume cleanly. A timestamped log appends to migration.log.

Inputs:  drive_migration_plan.PLAN  (list of Action dataclasses)
Outputs: stdout status, structured log to migration.log

Safety:
    - Read-only on C:, D:, F: — only writes to E:\\_migration\\.
    - Originals are never moved or deleted; only copied.
    - Reparse points (Windows symlinks/junctions) are skipped to avoid loops.
    - Per-file errors are logged and the run continues.
    - State file lets re-runs skip already-completed actions.
"""
import argparse
import fnmatch
import io
import json
import os
import shutil
import stat as stat_mod
import sys
import time
from datetime import datetime
from pathlib import Path

FILE_ATTRIBUTE_REPARSE_POINT = 0x400  # Windows reparse point flag (junctions + cloud placeholders)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
import drive_migration_plan as plan_module

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "migration.state.json"
LOG_FILE = SCRIPT_DIR / "migration.log"

# Patterns matched by basename — applied to every copy in addition to per-action excludes
GLOBAL_EXCLUDES = [
    "$RECYCLE.BIN",
    "System Volume Information",
    "Thumbs.db",
    "desktop.ini",
    ".DS_Store",
]


def fmt_size(n: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def matches(name: str, patterns: list[str]) -> bool:
    for p in patterns:
        if fnmatch.fnmatch(name, p) or p == name:
            return True
    return False


def is_reparse_point(path: Path) -> bool:
    """True for junctions, symlinks, and cloud-only placeholders on Windows."""
    try:
        st = path.stat(follow_symlinks=False)
        attrs = getattr(st, "st_file_attributes", 0)
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except (OSError, AttributeError):
        return False


def safe_copytree(src: Path, dest: Path, excludes: list[str]) -> tuple[int, list[str]]:
    """Copy src tree to dest, skipping reparse points and unreadable items.

    Returns (files_copied, list_of_skipped_paths_with_reason).
    Tolerates per-file OSError (cloud placeholders, junctions, access-denied
    subdirs) and continues. shutil.copytree's all-or-nothing behavior is too
    brittle for a real Windows user-profile tree.
    """
    skipped: list[str] = []
    files_copied = 0

    if src.is_file():
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            return 1, []
        except OSError as e:
            return 0, [f"{src}: {e}"]

    def on_walk_error(err: OSError) -> None:
        skipped.append(f"{getattr(err, 'filename', '?')}: {err.strerror or err}")

    for root, dirs, files in os.walk(src, onerror=on_walk_error):
        root_p = Path(root)
        new_dirs = []
        for d in dirs:
            full = root_p / d
            if matches(d, excludes):
                continue
            if is_reparse_point(full):
                skipped.append(f"{full}: reparse point (junction/cloud placeholder)")
                continue
            new_dirs.append(d)
        dirs[:] = new_dirs

        rel = root_p.relative_to(src)
        dest_dir = dest / rel
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            skipped.append(f"{dest_dir}: {e}")
            continue

        for f in files:
            if matches(f, excludes):
                continue
            full = root_p / f
            if is_reparse_point(full):
                skipped.append(f"{full}: reparse point (cloud placeholder)")
                continue
            target = dest_dir / f
            try:
                # Idempotency: skip files already copied at the same size.
                # Lets a re-run after a failed action skip already-copied bulk.
                if target.exists() and target.stat().st_size == full.stat().st_size:
                    files_copied += 1
                    continue
                shutil.copy2(full, target)
                files_copied += 1
            except OSError as e:
                skipped.append(f"{full}: {e}")

    return files_copied, skipped


def compute_size(path: Path, excludes: list[str]) -> tuple[int, int, int]:
    """Walk path, return (total_bytes, file_count, error_count)."""
    if not path.exists():
        return 0, 0, 0
    if path.is_file():
        try:
            return path.stat().st_size, 1, 0
        except OSError:
            return 0, 0, 1
    total = 0
    files = 0
    errors = 0
    try:
        walker = path.walk(on_error=lambda e: None)
    except AttributeError:
        # Path.walk requires Python 3.12+; fall back to os.walk
        import os
        def walker_fn():
            for root, dirs, fs in os.walk(path, onerror=lambda e: None):
                yield Path(root), dirs, fs
        walker = walker_fn()
    for root, dirs, file_list in walker:
        # Filter dirs in place — also prevents descent into excluded subtrees
        dirs[:] = [d for d in dirs if not matches(d, excludes)]
        for f in file_list:
            if matches(f, excludes):
                continue
            try:
                total += (root / f).stat().st_size
                files += 1
            except OSError:
                errors += 1
    return total, files, errors


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"completed": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def action_id(action) -> str:
    return f"{action.kind}|{action.source}|{action.dest}"


def log(msg: str, fh) -> None:
    print(msg)
    if fh is not None:
        fh.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")
        fh.flush()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase A drive migration: stage C:/F: personal data onto E:.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--execute", action="store_true",
                        help="actually perform actions (default is dry-run)")
    parser.add_argument("--force", action="store_true",
                        help="re-run actions already marked completed in state file")
    args = parser.parse_args()

    fh = LOG_FILE.open("a", encoding="utf-8", newline="")
    state = load_state()
    completed = set(state["completed"])

    plan = plan_module.PLAN
    mode = "EXECUTE" if args.execute else "DRY-RUN"

    log("", fh)
    log("=" * 78, fh)
    log(f"drive_migration_stage.py — {mode}  ({datetime.now().isoformat(timespec='seconds')})", fh)
    log(f"Plan has {len(plan)} actions. State file: {STATE_FILE}", fh)
    log("=" * 78, fh)

    n_copy_planned = 0
    n_copy_done = 0
    n_copy_err = 0
    n_skip = 0
    n_review = 0
    total_size = 0
    total_files = 0

    for i, action in enumerate(plan, start=1):
        excludes = GLOBAL_EXCLUDES + (action.excludes or [])
        key = action_id(action)
        already_done = key in completed and not args.force

        log("", fh)
        log(f"[{i:02d}/{len(plan)}] {action.kind.upper():6s}  {action.description}", fh)
        log(f"        source: {action.source}", fh)
        if action.dest:
            log(f"        dest:   {action.dest}", fh)

        if action.kind == "skip":
            log(f"        → skip (no action)", fh)
            n_skip += 1
            continue

        source = Path(action.source)

        if not source.exists():
            log(f"        ⚠ source does not exist; skipping", fh)
            continue

        if action.kind == "review":
            log(f"        computing size for review...", fh)
            size, files, errs = compute_size(source, excludes)
            log(f"        size: {fmt_size(size)}  ({files:,} files, {errs} stat errors)", fh)
            log(f"        → REVIEW: change action to 'copy' or 'skip' in drive_migration_plan.py", fh)
            n_review += 1
            continue

        # action.kind == "copy"
        n_copy_planned += 1
        dest = Path(action.dest)

        if already_done:
            log(f"        → already completed (state file); use --force to redo", fh)
            n_copy_done += 1
            continue

        log(f"        computing size...", fh)
        size, files, errs = compute_size(source, excludes)
        log(f"        size: {fmt_size(size)}  ({files:,} files, {errs} stat errors)", fh)
        total_size += size
        total_files += files

        if dest.exists():
            log(f"        ⚠ dest already exists; will merge with existing content", fh)

        if not args.execute:
            log(f"        → would copy", fh)
            continue

        log(f"        copying...", fh)
        t0 = time.time()
        try:
            files_copied, skipped = safe_copytree(source, dest, excludes)
            elapsed = max(time.time() - t0, 0.001)
            rate = size / elapsed
            log(f"        ✓ copied {files_copied:,} files in {elapsed:,.1f}s  ({fmt_size(rate)}/s)", fh)
            if skipped:
                log(f"        ⚠ {len(skipped)} item(s) skipped (reparse points / access denied / cloud placeholders):", fh)
                for s in skipped:
                    log(f"          - {s}", fh)
            completed.add(key)
            state["completed"] = sorted(completed)
            save_state(state)
            n_copy_done += 1
        except Exception as e:
            log(f"        ✗ copy failed: {e}", fh)
            n_copy_err += 1

    log("", fh)
    log("=" * 78, fh)
    log(f"Summary ({mode}):", fh)
    log(f"  copy actions:   {n_copy_planned:>4d} planned, {n_copy_done:>4d} done, {n_copy_err:>4d} errored", fh)
    log(f"  skipped:        {n_skip:>4d}", fh)
    log(f"  review pending: {n_review:>4d}", fh)
    log(f"  data size:      {fmt_size(total_size)} across {total_files:,} files", fh)
    if not args.execute:
        log(f"  (dry-run — no writes performed; re-run with --execute to copy)", fh)
    log("=" * 78, fh)

    fh.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""restore.py — Pull staged Windows data off the old NTFS drive into Linux.

Reads the Phase A staging tree produced by
projects/desktop-homelab/tools/drive_migration_stage.py (63.85 GB / 329,712
files as of 2026-10-07) and copies the portable parts into place on the new
system. The source drive is only ever read.

Safety model — never destructive:
    - Files that already exist at the destination are SKIPPED, not overwritten,
      unless --overwrite is passed. This is what makes merging into a live
      ~/.claude safe: config written by a fresh Claude Code install wins, and
      only files absent from the new machine get restored.
    - The source tree is opened read-only. Nothing is moved or deleted.
    - Dry-run by default.

Not everything staged is restorable. AppData/Roaming is Windows application
state and means nothing to Linux — it is kept on the NAS as an archive to mine
for licence keys, not copied into $HOME. The tool says so rather than silently
skipping.

The staging tree is a UNION, not a snapshot. drive_migration_stage.py merges on
re-run and never deletes, so a tree staged in May 2026 and re-staged in October
contains files from both states. Measured 2026-10-07: the staged .claude had
1,164 files against 698 live — 466 were session transcripts and subagent logs
deleted in the intervening months. Two consequences:
    - Upside: anything deleted by accident since the first staging run is still
      recoverable here.
    - Downside: restoring resurrects that history. Harmless for Documents or
      Pictures; cluttering for ~/.claude. Restore `claude` only if you want the
      old transcripts back, and prefer --only home for a clean start.

Usage:
    # Find the staging tree and show what would happen (default)
    python3 bootstrap/restore.py

    # Point at the mount explicitly
    python3 bootstrap/restore.py --source /srv/nas/_migration

    # Restore the personal data
    python3 bootstrap/restore.py --execute --only home,claude

    # Everything portable
    python3 bootstrap/restore.py --execute

Inputs:  _migration/ staging tree on the mounted old E: drive
Outputs: per-group progress and byte counts on stdout; nonzero exit on failure
"""
import argparse
import io
import shutil
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

HOME = Path.home()

# group -> (source subpath, destination, note)
# Destinations are deliberately conservative: personal data into $HOME, bulk
# archives left on the NAS for Phase B consolidation.
MAPPINGS: dict[str, list[tuple[str, Path, str]]] = {
    "home": [
        ("C-chipj/Documents", HOME / "Documents", ""),
        ("C-chipj/Desktop", HOME / "Desktop", ""),
        ("C-chipj/Pictures", HOME / "Pictures", ""),
        ("C-chipj/Music", HOME / "Music", ""),
        ("C-chipj/Videos", HOME / "Videos", ""),
        ("C-chipj/Favorites", HOME / "Documents" / "windows-favorites", "legacy IE/Edge bookmarks"),
        ("C-chipj/Apple", HOME / "Documents" / "apple-icloud-archive", "6.6 GB iCloud sync data"),
        ("C-chipj/OneDrive", HOME / "Documents" / "onedrive-archive",
         "3 online-only placeholders never staged; they remain in the cloud"),
    ],
    "claude": [
        ("C-chipj/.claude", HOME / ".claude",
         "merges — fresh-install files are kept. NOTE: the staged tree is a union "
         "of every staging run, so this also restores ~466 session transcripts and "
         "subagent logs deleted between May and Oct 2026. Skip this group if you "
         "want a clean history; memory/ is the part actually worth recovering."),
    ],
    "dotfiles": [
        ("C-chipj/.config", HOME / ".config", "merges"),
        ("C-chipj/.ipython", HOME / ".ipython", ""),
        ("C-chipj/.jupyter", HOME / ".jupyter", ""),
        ("C-chipj/.vscode", HOME / ".vscode", ""),
    ],
    "archive": [
        ("F-Chip", None, "old F: user profile — Phase B consolidation target"),
        ("F-Chip-Pictures", None, "7.9 GB — merge into the master photo collection in Phase B"),
        ("F-voice-memos", None, "263 MB m4a — destined for /srv/media"),
        ("F-Cadence", None, "17.5 GB EDA install + pedal designs"),
        ("F-EAGLE-7.6.0", None, "278 MB EDA"),
        ("F-Chess Openings Files", None, ""),
        ("F-_local.git", None, "old local git repos"),
    ],
}

# Staged but deliberately not restored, with the reason.
NOT_RESTORED = [
    ("C-chipj/AppData/Roaming",
     "Windows application state — meaningless on Linux. Keep on the NAS as an "
     "archive to mine for licence keys and app settings; do not copy to $HOME."),
    ("C-chipj/.gitconfig",
     "bootstrap.py writes a fresh one from will-personal/config.json. Restoring "
     "this would fight it. Diff it by hand if you had custom aliases."),
    ("C-chipj/Muse Hub", "app install state — reinstall MuseScore instead."),
    ("C-chipj/Intel", "driver logs, empty."),
    ("C-chipj/source", "empty Visual Studio folder."),
]

GROUPS = tuple(MAPPINGS)


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


def find_source() -> Path | None:
    """Locate the _migration staging tree on a mounted NTFS volume."""
    candidates: list[Path] = []
    roots = [Path("/srv"), Path("/mnt"), Path("/media"), Path("/media") / (HOME.name)]
    for root in roots:
        if not root.is_dir():
            continue
        direct = root / "_migration"
        if direct.is_dir():
            candidates.append(direct)
        try:
            for child in root.iterdir():
                if child.is_dir() and (child / "_migration").is_dir():
                    candidates.append(child / "_migration")
        except PermissionError:
            continue
    return candidates[0] if candidates else None


def copy_tree(src: Path, dst: Path, execute: bool, overwrite: bool) -> tuple[int, int, int, list[str]]:
    """Copy src into dst. Returns (copied, skipped_existing, bytes, errors)."""
    copied = skipped = total = 0
    errors: list[str] = []

    for path in src.rglob("*"):
        if path.is_dir():
            continue
        try:
            rel = path.relative_to(src)
        except ValueError:
            continue
        target = dst / rel
        try:
            if target.exists() and not overwrite:
                skipped += 1
                continue
            size = path.stat().st_size
            if execute:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            copied += 1
            total += size
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    return copied, skipped, total, errors


def main() -> int:
    p = argparse.ArgumentParser(
        description="Restore staged Windows data onto the new Linux system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--source", help="path to the _migration tree (auto-detected if omitted)")
    p.add_argument("--execute", action="store_true", help="actually copy (default is dry-run)")
    p.add_argument("--overwrite", action="store_true",
                   help="overwrite files that already exist at the destination")
    p.add_argument("--only", default="", help=f"comma-separated subset of: {','.join(GROUPS)}")
    args = p.parse_args()

    source = Path(args.source).expanduser() if args.source else find_source()
    if source is None:
        print("ERROR: could not find a _migration tree.", file=sys.stderr)
        print("       Mount the old E: drive and pass --source, e.g.:", file=sys.stderr)
        print("         sudo mkdir -p /srv/nas", file=sys.stderr)
        print("         sudo mount -t ntfs3 -o ro /dev/sdXN /srv/nas", file=sys.stderr)
        print("         python3 bootstrap/restore.py --source /srv/nas/_migration", file=sys.stderr)
        return 2
    if not source.is_dir():
        print(f"ERROR: {source} is not a directory.", file=sys.stderr)
        return 2

    selected = [s.strip() for s in args.only.split(",") if s.strip()] or list(GROUPS)
    unknown = [s for s in selected if s not in GROUPS]
    if unknown:
        print(f"ERROR: unknown group(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"       valid: {', '.join(GROUPS)}", file=sys.stderr)
        return 2

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print("=" * 74)
    print(f"will restore — {mode}")
    print(f"source: {source}")
    print(f"groups: {', '.join(selected)}")
    if args.overwrite:
        print("OVERWRITE IS ON — existing destination files will be replaced.")
    else:
        print("existing destination files are skipped (pass --overwrite to replace)")
    if not args.execute:
        print("\nNothing will be copied. Re-run with --execute to apply.")
    print("=" * 74)

    grand_copied = grand_skipped = grand_bytes = 0
    all_errors: list[str] = []

    for group in selected:
        print(f"\n==> {group}")
        for sub, dest, note in MAPPINGS[group]:
            src = source / sub
            if not src.is_dir():
                print(f"    --  {sub}: not present in staging")
                continue
            if dest is None:
                size = sum(f.stat().st_size for f in src.rglob("*") if f.is_file())
                print(f"    ##  {sub}: {human(size)} — stays on the NAS")
                if note:
                    print(f"          {note}")
                continue
            copied, skipped, nbytes, errors = copy_tree(src, dest, args.execute, args.overwrite)
            verb = "copied" if args.execute else "would copy"
            print(f"    OK  {sub} -> {dest}")
            print(f"          {verb} {copied} files ({human(nbytes)}), "
                  f"{skipped} already present")
            if note:
                print(f"          {note}")
            if errors:
                print(f"          {len(errors)} error(s); first: {errors[0]}")
            grand_copied += copied
            grand_skipped += skipped
            grand_bytes += nbytes
            all_errors.extend(errors)

    print("\n==> Staged but deliberately NOT restored")
    for sub, reason in NOT_RESTORED:
        if (source / sub).exists():
            print(f"    !!  {sub}")
            print(f"          {reason}")

    print()
    print("=" * 74)
    verb = "Copied" if args.execute else "Would copy"
    print(f"{verb}: {grand_copied} files, {human(grand_bytes)}")
    print(f"Already present (skipped): {grand_skipped}")
    print(f"Errors: {len(all_errors)}")
    if all_errors:
        print("\nFirst 10 errors:")
        for e in all_errors[:10]:
            print(f"  - {e}")
    print("=" * 74)

    if args.execute and "claude" in selected:
        print("\nNote: ~/.claude was merged, not replaced. If memory or settings look")
        print("wrong, compare against the staged copy before editing.")

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())

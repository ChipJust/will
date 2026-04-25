#!/usr/bin/env python3
"""commit_push.py — Stage specific files, commit, and push, in one approved call.

Replaces the `git add ... && git commit -m ... && git push` chain with a single
pre-approved CLI invocation, eliminating per-step permission prompts.

Usage:
    uv run python D:/_code/will/tools/commit_push.py <repo> <file> [<file>...] -m <message> [--no-push] [--allow-empty]

Examples:
    uv run python D:/_code/will/tools/commit_push.py D:/_code/money tools/foo.py -m "Fix foo"
    uv run python D:/_code/will/tools/commit_push.py D:/_code/will HANDOFF.md PLAN.md -m "$(cat <<'EOF'
    Update handoff and plan

    Body line.
    EOF
    )"

Safety guarantees:
    - Refuses files matching common secret patterns (.env*, *.pem, *.key,
      credentials*, secrets*, id_rsa*, id_ed25519*).
    - Refuses files outside the specified repo.
    - Refuses directories — only specific files are accepted.
    - Refuses an empty staged diff (unless --allow-empty).
    - Refuses detached-HEAD commits.
    - Subprocess calls use arg lists (no shell expansion).
    - No --force, --no-verify, --amend, or any other flag passthrough — the
      tool only ever runs `git add -- <files>`, `git commit -m <msg>`, and
      `git push`. There is no way for a caller to inject other flags.

Inputs:  repo path, list of file paths, commit message string.
Outputs: status lines on stdout; nonzero exit on failure.
"""
import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

SECRET_PATTERNS = [
    re.compile(r"\.env(\..+)?$", re.IGNORECASE),
    re.compile(r".+\.pem$", re.IGNORECASE),
    re.compile(r".+\.key$", re.IGNORECASE),
    re.compile(r".+\.pfx$", re.IGNORECASE),
    re.compile(r"id_rsa.*", re.IGNORECASE),
    re.compile(r"id_ed25519.*", re.IGNORECASE),
    re.compile(r"credentials.*\.json$", re.IGNORECASE),
    re.compile(r"secrets?\.(yaml|yml|json|toml)$", re.IGNORECASE),
]


def run(args, cwd, check=True):
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, check=check, encoding="utf-8"
    )


def is_secret(rel_path: str) -> bool:
    base = rel_path.replace("\\", "/").split("/")[-1]
    return any(p.match(base) for p in SECRET_PATTERNS)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Stage files, commit, push — single approved tool call.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("repo", help="absolute path to the git repo")
    p.add_argument("files", nargs="+", help="files to stage (relative to repo or absolute)")
    p.add_argument("-m", "--message", required=True, help="commit message")
    p.add_argument("--no-push", action="store_true", help="commit only; do not push")
    p.add_argument("--allow-empty", action="store_true", help="allow empty staged diff")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: not a git repo: {repo}", file=sys.stderr)
        return 2

    if not args.message.strip():
        print("ERROR: commit message is empty", file=sys.stderr)
        return 2

    file_paths = []
    for f in args.files:
        candidate = (repo / f) if not Path(f).is_absolute() else Path(f)
        candidate = candidate.resolve()
        try:
            rel = candidate.relative_to(repo)
        except ValueError:
            print(f"ERROR: {f!r} is outside repo {repo}", file=sys.stderr)
            return 2
        if not candidate.exists():
            print(f"ERROR: {f!r} does not exist (resolved: {candidate})", file=sys.stderr)
            return 2
        if candidate.is_dir():
            print(f"ERROR: {f!r} is a directory; pass specific files only", file=sys.stderr)
            return 2
        rel_posix = rel.as_posix()
        if is_secret(rel_posix):
            print(f"ERROR: {rel_posix} matches a secret pattern; refusing", file=sys.stderr)
            return 2
        file_paths.append(rel_posix)

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).stdout.strip()
    if branch == "HEAD":
        print("ERROR: detached HEAD; refusing to commit", file=sys.stderr)
        return 2

    print(f"Repo:   {repo}")
    print(f"Branch: {branch}")
    print(f"Staging {len(file_paths)} file(s):")
    for fp in file_paths:
        print(f"  + {fp}")
    run(["git", "add", "--"] + file_paths, cwd=repo)

    diff = run(["git", "diff", "--cached", "--stat"], cwd=repo).stdout.strip()
    if not diff and not args.allow_empty:
        print("ERROR: nothing staged (file unchanged?). Pass --allow-empty if intentional.", file=sys.stderr)
        return 2
    if diff:
        print("Staged diff:")
        for line in diff.splitlines():
            print(f"  {line}")

    cp = run(["git", "commit", "-m", args.message], cwd=repo, check=False)
    if cp.returncode != 0:
        print(f"ERROR: commit failed (rc={cp.returncode})", file=sys.stderr)
        if cp.stdout.strip():
            print(cp.stdout, file=sys.stderr)
        if cp.stderr.strip():
            print(cp.stderr, file=sys.stderr)
        return 1

    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo).stdout.strip()
    print(f"Committed: {head}")

    if args.no_push:
        return 0

    cp = run(["git", "push"], cwd=repo, check=False)
    if cp.returncode != 0:
        print(f"ERROR: push failed (rc={cp.returncode})", file=sys.stderr)
        if cp.stderr.strip():
            print(cp.stderr.strip(), file=sys.stderr)
        return 1

    out = (cp.stdout + cp.stderr).strip()
    if out:
        for line in out.splitlines():
            print(f"  {line}")
    print("Pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

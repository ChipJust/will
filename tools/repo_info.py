#!/usr/bin/env python3
"""repo_info.py — Show recent git log, status, and/or diff for a repo.

Replaces the `cd <repo> && git log ... && git status ...` chain with a single
pre-approved CLI call, eliminating per-step permission prompts.

Usage:
    uv run python D:/_code/will/tools/repo_info.py <repo> [options]

Examples:
    uv run python D:/_code/will/tools/repo_info.py D:/_code/home
    uv run python D:/_code/will/tools/repo_info.py D:/_code/home -n 5
    uv run python D:/_code/will/tools/repo_info.py D:/_code/home --status --diff
    uv run python D:/_code/will/tools/repo_info.py D:/_code/home --all

Options:
    -n, --count N       Number of recent commits to show (default: 15)
    --log               Show git log (default if no flags given)
    --status            Show git status
    --diff              Show git diff (staged + unstaged)
    --all               Show log + status + diff

Inputs:  repo path, optional flags.
Outputs: formatted git output on stdout; nonzero exit on failure.
"""
import argparse
import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def run(args, cwd):
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(
        description="Show git log/status/diff for a repo — single approved call.",
    )
    p.add_argument("repo", help="absolute path to the git repo")
    p.add_argument("-n", "--count", type=int, default=15, help="commits to show (default 15)")
    p.add_argument("--log", action="store_true", help="show git log")
    p.add_argument("--status", action="store_true", help="show git status")
    p.add_argument("--diff", action="store_true", help="show git diff")
    p.add_argument("--all", action="store_true", help="show log + status + diff")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: not a git repo: {repo}", file=sys.stderr)
        return 2

    if args.all:
        args.log = args.status = args.diff = True
    if not (args.log or args.status or args.diff):
        args.log = True

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).stdout.strip()
    print(f"Repo:   {repo}")
    print(f"Branch: {branch}")

    if args.log:
        print(f"\n── log (last {args.count}) ──")
        out = run(["git", "log", f"--oneline", f"-{args.count}"], cwd=repo).stdout.strip()
        print(out if out else "(no commits)")

    if args.status:
        print("\n── status ──")
        out = run(["git", "status", "--short"], cwd=repo).stdout.strip()
        print(out if out else "(clean)")

    if args.diff:
        print("\n── diff ──")
        out = run(["git", "diff"], cwd=repo).stdout.strip()
        staged = run(["git", "diff", "--cached"], cwd=repo).stdout.strip()
        if staged:
            print("(staged)")
            print(staged)
        if out:
            if staged:
                print("\n(unstaged)")
            print(out)
        if not out and not staged:
            print("(no changes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

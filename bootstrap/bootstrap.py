#!/usr/bin/env python3
"""bootstrap.py — Configure a fresh Linux machine as a will workstation.

Supersedes bootstrap/setup.sh. Installs git, gh, Node.js, uv and Claude Code,
authenticates GitHub, loads config from will-personal, configures git, clones
the repo set, syncs Python environments, and installs Claude Code plugins.

Runs on the system python3 with **stdlib only** — it has to work before uv
exists. Ubuntu ships python3, so there is nothing to install first.

Usage:
    # Preview every action; nothing is changed (default)
    python3 bootstrap/bootstrap.py

    # Actually do it
    python3 bootstrap/bootstrap.py --execute

    # Skip phases
    python3 bootstrap/bootstrap.py --execute --skip-clone --skip-plugins

Design notes — why this exists rather than the old setup.sh:
    - **No `curl | bash`.** The old script piped NodeSource, nvm and the uv
      installer straight into a shell, which contradicts the security posture
      in projects/desktop-homelab/STATUS.md. Node now comes from the Ubuntu
      archive and uv from pipx. The only curl call left fetches GitHub's apt
      signing key, which is then used to *verify* packages — that is a signed
      repo, not an unsigned script.
    - **One Node strategy.** The old pair of scripts used NodeSource in one and
      nvm in the other.
    - **Failures do not cascade.** `set -euo pipefail` meant one missing repo
      aborted the whole run. Here each step is independent and the summary
      reports what failed.
    - **npm prefix is user-local**, so `npm install -g` never needs sudo.

Inputs:  will-personal/config.json (git.name, git.email, workspace.linux, repos[])
Outputs: step status on stdout; nonzero exit if any step failed.
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

WILL_DIR = Path(__file__).resolve().parent.parent
NPM_PREFIX = Path.home() / ".npm-global"

# Collected outcomes, printed as the final summary.
RESULTS: list[tuple[str, str, str]] = []  # (status, step, detail)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def step(msg: str) -> None:
    print(f"\n==> {msg}")


def record(status: str, name: str, detail: str = "") -> None:
    RESULTS.append((status, name, detail))
    marker = {"ok": "    OK  ", "skip": "    --  ", "fail": "    !!  ", "plan": "    ..  "}[status]
    print(f"{marker}{name}{(': ' + detail) if detail else ''}")


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------
def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(args: list[str], check: bool = True, capture: bool = True, env=None) -> subprocess.CompletedProcess:
    """Run a command with an argument list. Never uses a shell."""
    return subprocess.run(
        args,
        check=check,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        env=env,
    )


def out(args: list[str]) -> str:
    try:
        return run(args).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def apt_install(packages: list[str], execute: bool) -> bool:
    if not execute:
        record("plan", "apt install " + " ".join(packages))
        return True
    try:
        run(["sudo", "apt-get", "install", "-y", "-q"] + packages, capture=False)
        return True
    except subprocess.CalledProcessError as exc:
        record("fail", "apt install " + " ".join(packages), str(exc))
        return False


# ---------------------------------------------------------------------------
# Phase 1 — base packages
# ---------------------------------------------------------------------------
def phase_base(execute: bool) -> None:
    step("[1/7] Base packages")

    if not have("apt-get"):
        record("fail", "package manager", "apt-get not found — this tool targets Ubuntu/Debian")
        return

    if execute:
        run(["sudo", "apt-get", "update", "-qq"], capture=False, check=False)

    # python3 is already present (we are running on it). unzip/ca-certificates
    # are cheap and routinely assumed by later steps.
    wanted = {
        "git": "git",
        "curl": "curl",
        "unzip": "unzip",
        "pipx": "pipx",
    }
    missing = [pkg for cmd, pkg in wanted.items() if not have(cmd)]
    if missing:
        apt_install(missing + ["ca-certificates"], execute)
        for cmd in wanted:
            if execute and have(cmd):
                record("ok", cmd, out([cmd, "--version"]).splitlines()[0] if have(cmd) else "")
    else:
        record("skip", "git, curl, unzip, pipx", "all present")


# ---------------------------------------------------------------------------
# Phase 2 — GitHub CLI from its signed apt repo
# ---------------------------------------------------------------------------
def phase_gh(execute: bool) -> None:
    step("[2/7] GitHub CLI")

    if have("gh"):
        record("skip", "gh", out(["gh", "--version"]).splitlines()[0])
        return

    if not execute:
        record("plan", "add cli.github.com apt repo + install gh")
        return

    keyring = "/usr/share/keyrings/githubcli-archive-keyring.gpg"
    try:
        # curl here fetches a *signing key*, which apt then uses to verify every
        # package from the repo. This is not the `curl | bash` pattern.
        key = run(["curl", "-fsSL", "https://cli.github.com/packages/githubcli-archive-keyring.gpg"]).stdout
        subprocess.run(["sudo", "tee", keyring], input=key, text=True, check=True, capture_output=True)
        run(["sudo", "chmod", "go+r", keyring])

        arch = out(["dpkg", "--print-architecture"])
        line = (
            f"deb [arch={arch} signed-by={keyring}] "
            "https://cli.github.com/packages stable main\n"
        )
        subprocess.run(
            ["sudo", "tee", "/etc/apt/sources.list.d/github-cli.list"],
            input=line, text=True, check=True, capture_output=True,
        )
        run(["sudo", "apt-get", "update", "-qq"], capture=False)
        apt_install(["gh"], execute)
        record("ok", "gh", out(["gh", "--version"]).splitlines()[0])
    except subprocess.CalledProcessError as exc:
        record("fail", "gh", f"{exc} — stderr: {getattr(exc, 'stderr', '')!r}")


# ---------------------------------------------------------------------------
# Phase 3 — Node.js, uv, Claude Code
# ---------------------------------------------------------------------------
def phase_toolchain(execute: bool) -> None:
    step("[3/7] Node.js (Ubuntu archive)")
    if have("node"):
        record("skip", "node", out(["node", "--version"]))
    else:
        apt_install(["nodejs", "npm"], execute)
        if execute and have("node"):
            record("ok", "node", out(["node", "--version"]))

    step("[4/7] uv (via pipx — no piped installer)")
    if have("uv"):
        record("skip", "uv", out(["uv", "--version"]))
    elif not execute:
        record("plan", "pipx install uv")
    elif have("pipx"):
        try:
            run(["pipx", "install", "uv"], capture=False)
            run(["pipx", "ensurepath"], check=False, capture=False)
            record("ok", "uv", "installed via pipx (may need a new shell for PATH)")
        except subprocess.CalledProcessError as exc:
            record("fail", "uv", str(exc))
    else:
        record("fail", "uv", "pipx unavailable; install pipx then re-run")

    step("[5/7] Claude Code (npm, user-local prefix)")
    if have("claude"):
        record("skip", "claude", "already installed")
        return
    if not execute:
        record("plan", f"npm prefix -> {NPM_PREFIX}, then npm install -g @anthropic-ai/claude-code")
        return
    if not have("npm"):
        record("fail", "claude", "npm not available")
        return
    try:
        # A user-local prefix keeps `npm install -g` out of /usr and away from sudo.
        NPM_PREFIX.mkdir(parents=True, exist_ok=True)
        run(["npm", "config", "set", "prefix", str(NPM_PREFIX)])
        ensure_path_line(f'export PATH="{NPM_PREFIX}/bin:$PATH"', execute)
        env = dict(os.environ, PATH=f"{NPM_PREFIX}/bin:{os.environ.get('PATH', '')}")
        run(["npm", "install", "-g", "@anthropic-ai/claude-code"], capture=False, env=env)
        record("ok", "claude", f"installed to {NPM_PREFIX}/bin")
    except subprocess.CalledProcessError as exc:
        record("fail", "claude", str(exc))


def ensure_path_line(line: str, execute: bool) -> None:
    """Append a PATH export to ~/.bashrc exactly once."""
    bashrc = Path.home() / ".bashrc"
    existing = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
    if line in existing:
        record("skip", "~/.bashrc", "PATH entry already present")
        return
    if not execute:
        record("plan", f"append to ~/.bashrc: {line}")
        return
    with bashrc.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"\n# added by will bootstrap\n{line}\n")
    record("ok", "~/.bashrc", "PATH entry added")


# ---------------------------------------------------------------------------
# Phase 4 — GitHub auth + config
# ---------------------------------------------------------------------------
def phase_auth(execute: bool) -> str | None:
    step("[6/7] GitHub authentication")

    if not have("gh"):
        record("fail", "gh auth", "gh not installed")
        return None

    authed = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True).returncode == 0
    if authed:
        record("skip", "gh auth", "already authenticated")
    elif not execute:
        record("plan", "gh auth login (interactive browser flow)")
        return None
    else:
        print("\n    gh auth login is interactive — follow the browser prompts.\n")
        try:
            subprocess.run(["gh", "auth", "login"], check=True)
        except subprocess.CalledProcessError as exc:
            record("fail", "gh auth login", str(exc))
            return None

    user = out(["gh", "api", "user", "-q", ".login"])
    if user:
        record("ok", "authenticated", user)

    # Make git use gh's credential helper for HTTPS remotes.
    if execute:
        try:
            run(["gh", "auth", "setup-git"])
            record("ok", "git credential helper", "configured via gh")
        except subprocess.CalledProcessError as exc:
            record("fail", "gh auth setup-git", str(exc))
    else:
        record("plan", "gh auth setup-git")

    return user or None


def load_config(user: str, workspace_default: Path, execute: bool) -> dict | None:
    """Clone will-personal if needed and read config.json out of it."""
    step("[7/7] Config from will-personal")

    personal_dir = workspace_default / "will-personal"
    config_path = personal_dir / "config.json"

    if config_path.exists():
        record("skip", "will-personal", f"already at {personal_dir}")
    else:
        repo = f"{user}/will-personal"
        if subprocess.run(["gh", "repo", "view", repo], capture_output=True).returncode != 0:
            record("fail", "will-personal", f"{repo} not found on GitHub — create it, then re-run")
            return None
        if not execute:
            record("plan", f"gh repo clone {repo} {personal_dir}")
            return None
        workspace_default.mkdir(parents=True, exist_ok=True)
        try:
            run(["gh", "repo", "clone", repo, str(personal_dir)], capture=False)
            record("ok", "will-personal", f"cloned to {personal_dir}")
        except subprocess.CalledProcessError as exc:
            record("fail", "will-personal clone", str(exc))
            return None

    if not config_path.exists():
        record("fail", "config.json", f"not found at {config_path}")
        return None

    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        record("fail", "config.json", f"invalid JSON: {exc}")
        return None

    record("ok", "config.json", f"{cfg.get('git', {}).get('name', '?')} | {len(cfg.get('repos', []))} repos")
    return cfg


# ---------------------------------------------------------------------------
# git config, repo cloning, uv sync, plugins
# ---------------------------------------------------------------------------
def configure_git(cfg: dict, execute: bool) -> None:
    step("Git configuration")
    settings = {
        "user.name": cfg.get("git", {}).get("name", ""),
        "user.email": cfg.get("git", {}).get("email", ""),
        "init.defaultBranch": "main",
        "core.autocrlf": "input",
        "pull.rebase": "false",
    }
    for key, value in settings.items():
        if not value:
            record("fail", f"git config {key}", "missing in config.json")
            continue
        current = out(["git", "config", "--global", key])
        if current == value:
            record("skip", f"git config {key}", value)
        elif not execute:
            record("plan", f"git config --global {key} {value}")
        else:
            run(["git", "config", "--global", key, value])
            record("ok", f"git config {key}", value)


def clone_repos(cfg: dict, user: str, workspace: Path, execute: bool) -> list[Path]:
    step(f"Cloning repos to {workspace}")
    cloned: list[Path] = []
    for name in cfg.get("repos", []):
        dest = workspace / name
        if (dest / ".git").is_dir():
            record("skip", name, "already cloned")
            cloned.append(dest)
            continue
        repo = f"{user}/{name}"
        if subprocess.run(["gh", "repo", "view", repo], capture_output=True).returncode != 0:
            # Known case: spatium is local-only and not on GitHub. The old shell
            # script aborted the entire run here; we note it and keep going.
            record("fail", name, "not found on GitHub — skipped, run continues")
            continue
        if not execute:
            record("plan", f"gh repo clone {repo} {dest}")
            continue
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            run(["gh", "repo", "clone", repo, str(dest)], capture=False)
            record("ok", name, "cloned")
            cloned.append(dest)
        except subprocess.CalledProcessError as exc:
            record("fail", f"clone {name}", str(exc))
    return cloned


def sync_repos(repos: list[Path], execute: bool) -> None:
    step("uv sync")
    if not have("uv"):
        record("fail", "uv sync", "uv not on PATH — open a new shell and re-run with --skip-clone")
        return
    for repo in repos:
        if not (repo / "pyproject.toml").is_file():
            record("skip", repo.name, "no pyproject.toml")
            continue
        if not execute:
            record("plan", f"uv sync in {repo}")
            continue
        try:
            subprocess.run(["uv", "sync"], cwd=repo, check=True, capture_output=True, text=True)
            record("ok", repo.name, "synced")
        except subprocess.CalledProcessError as exc:
            record("fail", f"uv sync {repo.name}", (exc.stderr or "")[-300:])


def install_plugins(execute: bool) -> None:
    step("Claude Code plugins")
    installer = WILL_DIR / "plugins" / "install.sh"
    if not installer.is_file():
        record("fail", "plugins", f"{installer} not found")
        return
    if not execute:
        record("plan", f"bash {installer}")
        return
    try:
        run(["bash", str(installer)], capture=False)
        record("ok", "plugins", "installed — restart Claude Code to pick them up")
    except subprocess.CalledProcessError as exc:
        record("fail", "plugins", str(exc))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(
        description="Bootstrap a fresh Linux machine as a will workstation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--execute", action="store_true", help="actually make changes (default is dry-run)")
    p.add_argument("--skip-clone", action="store_true", help="skip repo cloning and uv sync")
    p.add_argument("--skip-plugins", action="store_true", help="skip Claude Code plugin install")
    args = p.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print("=" * 74)
    print(f"will bootstrap — {mode}")
    print(f"will repo: {WILL_DIR}")
    print(f"python:    {sys.version.split()[0]}")
    if not args.execute:
        print("\nNothing will be changed. Re-run with --execute to apply.")
    print("=" * 74)

    phase_base(args.execute)
    phase_gh(args.execute)
    phase_toolchain(args.execute)
    user = phase_auth(args.execute)

    workspace = Path.home() / "code"
    cfg = load_config(user, workspace, args.execute) if user else None

    if cfg:
        ws = cfg.get("workspace", {}).get("linux", "~/code")
        workspace = Path(os.path.expanduser(ws))
        configure_git(cfg, args.execute)
        if not args.skip_clone:
            repos = clone_repos(cfg, user, workspace, args.execute)
            sync_repos(repos, args.execute)
    if not args.skip_plugins:
        install_plugins(args.execute)

    # ---- summary ----
    failed = [r for r in RESULTS if r[0] == "fail"]
    print()
    print("=" * 74)
    counts = {s: sum(1 for r in RESULTS if r[0] == s) for s in ("ok", "skip", "plan", "fail")}
    print(f"Summary ({mode}):  ok={counts['ok']}  skipped={counts['skip']}  "
          f"planned={counts['plan']}  failed={counts['fail']}")
    if failed:
        print("\nFailed steps:")
        for _, name, detail in failed:
            print(f"  - {name}{(': ' + detail) if detail else ''}")
    print("=" * 74)

    if args.execute:
        print("\nNext:")
        print("  1. source ~/.bashrc   (or open a new terminal) — picks up uv and claude on PATH")
        print("  2. python3 bootstrap/harden.py          — review the security setup")
        print("  3. python3 bootstrap/restore.py --help  — pull staged data off the old drive")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

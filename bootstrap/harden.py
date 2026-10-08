#!/usr/bin/env python3
"""harden.py — Apply the desktop-homelab security posture to a fresh Ubuntu box.

Implements the decisions recorded in projects/desktop-homelab/STATUS.md and
ADR 0006: no host antivirus, signed repos only, automatic security updates,
default-deny firewall with the tailnet as the only ingress, key-only SSH.

Deliberately NOT here:
    - Antivirus. There is no host AV on this machine by decision. ClamAV is a
      Phase B item scoped to scanning /srv/nas so the Samba share does not
      carry Windows/Mac malware to family machines — file-server hygiene, not
      host defence. It is not a day-one step.
    - LUKS. Declined in ADR 0006; it is install-time-only anyway.
    - gocryptfs/fscrypt over the sensitive NAS trees. That is ADR 0006's Phase B
      obligation and needs /srv/nas to exist first.

Two safety interlocks, because both of these failure modes lock you out:
    - Refuses to enable UFW while you are connected over SSH unless you pass
      --force-remote. A default-deny policy applied over SSH before Tailscale
      is up ends the session and you cannot get back in.
    - Refuses to disable SSH password authentication unless a non-empty
      ~/.ssh/authorized_keys already exists. Otherwise you lock yourself out of
      the only remaining login path.

Usage:
    # Preview everything; nothing is changed (default)
    python3 bootstrap/harden.py

    # Apply
    sudo -v && python3 bootstrap/harden.py --execute

    # Individual phases
    python3 bootstrap/harden.py --execute --only updates,firewall

Inputs:  none (reads system state)
Outputs: step status on stdout; nonzero exit if any step failed.
"""
import argparse
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

RESULTS: list[tuple[str, str, str]] = []

PHASES = ("updates", "firewall", "ssh", "tailscale", "audit")

UNATTENDED_CONF = Path("/etc/apt/apt.conf.d/52will-unattended-upgrades")
UNATTENDED_BODY = """// Managed by will/bootstrap/harden.py
// Always-on homelab: apply security updates and reboot in the small hours.
// Unattended reboot only works because ADR 0006 declined LUKS -- there is no
// passphrase prompt to block the boot.
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
"""

SSHD_CONF = Path("/etc/ssh/sshd_config.d/99-will-hardening.conf")
SSHD_BODY = """# Managed by will/bootstrap/harden.py
# Key-only SSH. Reachable over the tailnet only -- see ufw rules.
PasswordAuthentication no
PermitRootLogin no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
X11Forwarding no
"""


def step(msg: str) -> None:
    print(f"\n==> {msg}")


def record(status: str, name: str, detail: str = "") -> None:
    RESULTS.append((status, name, detail))
    marker = {"ok": "    OK  ", "skip": "    --  ", "fail": "    !!  ",
              "plan": "    ..  ", "warn": "    ??  "}[status]
    print(f"{marker}{name}{(': ' + detail) if detail else ''}")


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(args: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, capture_output=capture, text=True, encoding="utf-8")


def out(args: list[str]) -> str:
    try:
        return run(args).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def write_root_file(path: Path, body: str, execute: bool, label: str) -> None:
    """Write a root-owned config file via sudo tee, idempotently."""
    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == body:
                record("skip", label, f"{path} already current")
                return
        except PermissionError:
            pass
    if not execute:
        record("plan", label, f"write {path}")
        return
    try:
        run(["sudo", "mkdir", "-p", str(path.parent)])
        subprocess.run(["sudo", "tee", str(path)], input=body, text=True,
                       check=True, capture_output=True)
        record("ok", label, f"wrote {path}")
    except subprocess.CalledProcessError as exc:
        record("fail", label, str(exc))


def over_ssh() -> bool:
    return bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))


# ---------------------------------------------------------------------------
def phase_updates(execute: bool) -> None:
    step("Automatic security updates")
    if not have("unattended-upgrade"):
        if not execute:
            record("plan", "apt install unattended-upgrades")
        else:
            try:
                run(["sudo", "apt-get", "install", "-y", "-q", "unattended-upgrades"], capture=False)
                record("ok", "unattended-upgrades", "installed")
            except subprocess.CalledProcessError as exc:
                record("fail", "unattended-upgrades", str(exc))
                return
    else:
        record("skip", "unattended-upgrades", "already installed")

    write_root_file(UNATTENDED_CONF, UNATTENDED_BODY, execute, "unattended config")

    if execute:
        run(["sudo", "systemctl", "enable", "--now", "unattended-upgrades"], check=False, capture=False)
        state = out(["systemctl", "is-enabled", "unattended-upgrades"])
        record("ok" if state == "enabled" else "warn", "unattended-upgrades service", state or "unknown")


def phase_firewall(execute: bool, force_remote: bool) -> None:
    step("Firewall — default deny inbound, tailnet allowed")

    if not have("ufw"):
        if not execute:
            record("plan", "apt install ufw")
        else:
            try:
                run(["sudo", "apt-get", "install", "-y", "-q", "ufw"], capture=False)
                record("ok", "ufw", "installed")
            except subprocess.CalledProcessError as exc:
                record("fail", "ufw", str(exc))
                return

    if over_ssh() and not force_remote:
        record("fail", "ufw", "you are on SSH — a default-deny policy would drop this "
                             "session. Run at the physical console, or pass --force-remote "
                             "if the tailnet is already up and you are connected over it.")
        return

    rules = [
        (["sudo", "ufw", "default", "deny", "incoming"], "default deny incoming"),
        (["sudo", "ufw", "default", "allow", "outgoing"], "default allow outgoing"),
        # Interface-scoped, not port-scoped: Samba, Navidrome and SSH become
        # reachable only across the tailnet. Nothing is exposed to the LAN.
        (["sudo", "ufw", "allow", "in", "on", "tailscale0"], "allow in on tailscale0"),
    ]
    for cmd, label in rules:
        if not execute:
            record("plan", label)
            continue
        try:
            run(cmd, capture=False)
            record("ok", label)
        except subprocess.CalledProcessError as exc:
            record("fail", label, str(exc))

    if not execute:
        record("plan", "ufw enable")
        return
    try:
        subprocess.run(["sudo", "ufw", "--force", "enable"], check=True, capture_output=True, text=True)
        record("ok", "ufw enabled")
        print(out(["sudo", "ufw", "status", "verbose"]))
    except subprocess.CalledProcessError as exc:
        record("fail", "ufw enable", str(exc))


def phase_ssh(execute: bool) -> None:
    step("SSH — key-only authentication")

    if not have("sshd") and not Path("/usr/sbin/sshd").exists():
        record("skip", "sshd", "openssh-server not installed — nothing to harden")
        return

    keys = Path.home() / ".ssh" / "authorized_keys"
    key_count = 0
    if keys.is_file():
        key_count = len([
            ln for ln in keys.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ])

    if key_count == 0:
        record("fail", "ssh hardening",
               f"{keys} is missing or empty. Disabling password auth now would lock "
               "you out. From your laptop run:  ssh-copy-id <user>@<host>  "
               "then verify key login works, then re-run.")
        return

    record("ok", "authorized_keys", f"{key_count} key(s) present")
    write_root_file(SSHD_CONF, SSHD_BODY, execute, "sshd hardening")

    if not execute:
        record("plan", "sshd -t && systemctl restart ssh")
        return
    try:
        run(["sudo", "sshd", "-t"])
        record("ok", "sshd config", "syntax valid")
    except subprocess.CalledProcessError as exc:
        record("fail", "sshd config", f"invalid, NOT restarting: {exc.stderr or exc}")
        return
    try:
        run(["sudo", "systemctl", "restart", "ssh"], capture=False)
        record("ok", "ssh restarted", "keep this session open until you verify a new login")
    except subprocess.CalledProcessError as exc:
        record("fail", "ssh restart", str(exc))


def phase_tailscale(execute: bool) -> None:
    step("Tailscale — from its apt repo, not the piped installer")

    if have("tailscale"):
        record("skip", "tailscale", out(["tailscale", "version"]).splitlines()[0] if out(["tailscale", "version"]) else "installed")
    else:
        codename = out(["lsb_release", "-cs"]) or "unknown"
        record("warn", "tailscale",
               f"not installed. Detected codename '{codename}'. Tailscale's upstream "
               "apt paths are per-release and this tool will not guess a URL it has "
               "not verified. Take the keyring + sources.list lines for this release "
               "from https://tailscale.com/download/linux — use the apt repo method, "
               "NOT the `curl | sh` script, so updates flow through apt.")
        return

    if not execute:
        record("plan", "tailscale up")
        return
    state = out(["tailscale", "status", "--json"])
    if '"BackendState":"Running"' in state.replace(" ", ""):
        record("skip", "tailscale up", "already connected")
    else:
        record("warn", "tailscale up", "run `sudo tailscale up` — interactive browser auth")


def phase_audit(execute: bool) -> None:
    step("Audit — what protects this machine")

    aa = out(["systemctl", "is-active", "apparmor"])
    record("ok" if aa == "active" else "warn", "AppArmor", aa or "unknown")
    if aa == "active":
        print("        Leave it on. When something misbehaves the internet will tell "
              "you to disable it;\n        write a profile exception instead.")

    helper = out(["git", "config", "--global", "credential.helper"])
    record("ok" if helper else "warn", "git credential helper", helper or "not set — run `gh auth setup-git`")

    third_party = sorted(Path("/etc/apt/sources.list.d").glob("*.list")) if Path("/etc/apt/sources.list.d").is_dir() else []
    record("ok", "third-party apt repos", f"{len(third_party)} configured")
    for f in third_party:
        print(f"        - {f.name}")
    if third_party:
        print("        Each is a party that can push root-level code here. Keep the list short.")

    print("\n    Not installed, by decision:")
    print("      - No host antivirus. Defence is signed repos + patching + default-deny")
    print("        + tailnet-only ingress, not a scanner.")
    print("      - ClamAV is Phase B, scoped to /srv/nas for share hygiene only.")
    print("\n    Largest remaining gap (STATUS.md): no backup destination for")
    print("    irreplaceable family data. Backups are the real ransomware control;")
    print("    no scanner substitutes for a restore.")


# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(
        description="Apply the desktop-homelab security posture.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--execute", action="store_true", help="actually make changes (default is dry-run)")
    p.add_argument("--only", default="", help=f"comma-separated subset of: {','.join(PHASES)}")
    p.add_argument("--force-remote", action="store_true",
                   help="allow enabling ufw while connected over SSH (you are on the tailnet)")
    args = p.parse_args()

    selected = [s.strip() for s in args.only.split(",") if s.strip()] or list(PHASES)
    unknown = [s for s in selected if s not in PHASES]
    if unknown:
        print(f"ERROR: unknown phase(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"       valid: {', '.join(PHASES)}", file=sys.stderr)
        return 2

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print("=" * 74)
    print(f"will harden — {mode}")
    print(f"phases: {', '.join(selected)}")
    if over_ssh():
        print("session: SSH (firewall phase will refuse without --force-remote)")
    else:
        print("session: local console")
    if not args.execute:
        print("\nNothing will be changed. Re-run with --execute to apply.")
    print("=" * 74)

    if "updates" in selected:
        phase_updates(args.execute)
    if "firewall" in selected:
        phase_firewall(args.execute, args.force_remote)
    if "ssh" in selected:
        phase_ssh(args.execute)
    if "tailscale" in selected:
        phase_tailscale(args.execute)
    if "audit" in selected:
        phase_audit(args.execute)

    failed = [r for r in RESULTS if r[0] == "fail"]
    counts = {s: sum(1 for r in RESULTS if r[0] == s) for s in ("ok", "skip", "plan", "fail", "warn")}
    print()
    print("=" * 74)
    print(f"Summary ({mode}):  ok={counts['ok']}  skipped={counts['skip']}  "
          f"planned={counts['plan']}  warn={counts['warn']}  failed={counts['fail']}")
    if failed:
        print("\nFailed / blocked steps:")
        for _, name, detail in failed:
            print(f"  - {name}{(': ' + detail) if detail else ''}")
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

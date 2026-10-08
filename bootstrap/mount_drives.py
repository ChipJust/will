#!/usr/bin/env python3
"""mount_drives.py — Give the carried-over NTFS drives persistent mount points.

A fresh Ubuntu install mounts only what you configured during partitioning.
The drives carried over from the Windows machine are left as unmounted
partitions: visible in GNOME Files, mountable on a click at
/media/<user>/<label>, and absent entirely from a headless boot. That is no
good for a box whose whole job is serving /srv/nas and running dev work out of
/workspace, so they need /etc/fstab entries.

Target layout (projects/desktop-homelab/STATUS.md):
    'Data'      D: 477 GB NVMe  -> /workspace    repos; ext4 conversion last
    'Old Data'  E: 2.8 TB HDD   -> /srv/nas      stays NTFS, family storage
    'Old C'     F: 224 GB SSD   -> /srv/media    ext4 in Phase B

Why this is a tool and not a wiki page: a wrong /etc/fstab line drops the next
boot into an emergency shell. Every entry written here carries `nofail` and a
short device timeout so a missing or dirty drive can never block boot, the
existing fstab is backed up first, and `findmnt --verify` runs before anything
is committed.

BEFORE YOU WIPE WINDOWS -- Fast Startup must be off. Windows "shut down" with
Fast Startup enabled is a hybrid hibernate: it leaves every NTFS volume with a
dirty flag, and ntfs3 will then refuse a read-write mount. On the source machine
(measured 2026-10-07: Fast Startup ON) run as Administrator:

    powercfg /h off

then reboot. `Restart` also works in a pinch -- a restart always performs a full
kernel shutdown and bypasses Fast Startup -- but `powercfg /h off` is the
reliable fix. If you skip this, /workspace and /srv/nas come up read-only and
the staged 63.85 GB on E: is unreachable for writing.

Usage:
    # Show what is present and what would be written (default)
    python3 bootstrap/mount_drives.py

    # Write fstab entries, reload, and mount
    sudo -v && python3 bootstrap/mount_drives.py --execute

    # Mount somewhere else
    python3 bootstrap/mount_drives.py --execute --map "Data=/srv/code"

Inputs:  lsblk -J output (block devices, labels, UUIDs)
Outputs: proposed/written fstab lines on stdout; nonzero exit on failure
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

FSTAB = Path("/etc/fstab")

# label -> mount point, from the desktop-homelab plan
DEFAULT_PLAN = {
    "Data": "/workspace",
    "Old Data": "/srv/nas",
    "Old C": "/srv/media",
}

# Recorded from Windows 2026-10-07, so a drive can still be identified if its
# label is ever changed. GPT partition GUID == Linux PARTUUID.
KNOWN_PARTUUID = {
    "6c6201ed-fd48-4951-9b9a-e6eaa1f22051": ("Data", "D: 477 GB NVMe"),
    "8851dc3f-4654-4516-9671-c0b072ea911e": ("Old Data", "E: 2.8 TB HDD"),
    "cbc7147a-02": ("Old C", "F: 224 GB SATA SSD (MBR)"),
}

NTFS_FSTYPES = {"ntfs", "ntfs3"}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, capture_output=True, text=True, encoding="utf-8")


def out(args: list[str]) -> str:
    try:
        return run(args).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def list_block_devices() -> list[dict]:
    """Flattened lsblk output: every partition with a filesystem."""
    raw = out(["lsblk", "-J", "-o", "NAME,PATH,FSTYPE,LABEL,UUID,PARTUUID,SIZE,MOUNTPOINT"])
    if not raw:
        return []
    try:
        tree = json.loads(raw).get("blockdevices", [])
    except json.JSONDecodeError:
        return []

    flat: list[dict] = []

    def walk(nodes):
        for node in nodes:
            if node.get("fstype"):
                flat.append(node)
            walk(node.get("children", []) or [])

    walk(tree)
    return flat


def fstab_entry(dev: dict, mountpoint: str, uid: int, gid: int) -> str:
    """One fstab line. nofail is mandatory -- see module docstring."""
    ident = f"UUID={dev['uuid']}" if dev.get("uuid") else f"PARTUUID={dev['partuuid']}"
    if dev.get("fstype") in NTFS_FSTYPES:
        opts = (f"defaults,uid={uid},gid={gid},umask=022,windows_names,"
                "nofail,x-systemd.device-timeout=10")
        fstype = "ntfs3"
    else:
        opts = "defaults,nofail,x-systemd.device-timeout=10"
        fstype = dev.get("fstype", "auto")
    return f"{ident}  {mountpoint}  {fstype}  {opts}  0  0"


def read_fstab() -> str:
    try:
        return FSTAB.read_text(encoding="utf-8")
    except (OSError, PermissionError):
        return ""


def main() -> int:
    p = argparse.ArgumentParser(
        description="Create persistent mounts for the carried-over drives.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--execute", action="store_true", help="write /etc/fstab and mount (default is dry-run)")
    p.add_argument("--map", action="append", default=[],
                   help="override a mapping, e.g. --map \"Data=/srv/code\" (repeatable)")
    args = p.parse_args()

    plan = dict(DEFAULT_PLAN)
    for item in args.map:
        if "=" not in item:
            print(f"ERROR: --map needs LABEL=/path, got {item!r}", file=sys.stderr)
            return 2
        label, _, mp = item.partition("=")
        plan[label.strip()] = mp.strip()

    if not hasattr(os, "getuid"):
        print("ERROR: this tool configures /etc/fstab and only runs on Linux.", file=sys.stderr)
        return 2
    uid, gid = os.getuid(), os.getgid()
    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print("=" * 74)
    print(f"will mount_drives — {mode}")
    print(f"mounting as uid={uid} gid={gid}")
    if not args.execute:
        print("\n/etc/fstab will not be touched. Re-run with --execute to apply.")
    print("=" * 74)

    devices = list_block_devices()
    if not devices:
        print("ERROR: lsblk returned nothing. Is this a Linux system?", file=sys.stderr)
        return 2

    print("\n==> Block devices with a filesystem")
    for d in devices:
        known = KNOWN_PARTUUID.get(d.get("partuuid") or "", ("", ""))[1]
        print(f"    {d['path']:<16} {d.get('fstype',''):<8} {d.get('size',''):>9}  "
              f"label={d.get('label') or '-':<12} {('<- ' + known) if known else ''}")
        if d.get("mountpoint"):
            print(f"                     already mounted at {d['mountpoint']}")

    existing = read_fstab()
    proposed: list[tuple[dict, str, str]] = []

    print("\n==> Planned mounts")
    for label, mountpoint in plan.items():
        match = next((d for d in devices if d.get("label") == label), None)
        if match is None:
            match = next(
                (d for d in devices
                 if KNOWN_PARTUUID.get(d.get("partuuid") or "", ("", ""))[0] == label),
                None,
            )
            if match:
                print(f"    ?? {label}: label not found, matched by PARTUUID instead")
        if match is None:
            print(f"    -- {label} -> {mountpoint}: no such device, skipping")
            continue
        if mountpoint in existing:
            print(f"    -- {label} -> {mountpoint}: already in /etc/fstab, leaving alone")
            continue
        line = fstab_entry(match, mountpoint, uid, gid)
        proposed.append((match, mountpoint, line))
        print(f"    OK {label} -> {mountpoint}  ({match['path']}, {match.get('fstype')})")
        print(f"       {line}")

    if not proposed:
        print("\nNothing to do.")
        return 0

    # Dirty-NTFS warning: the single most likely reason a mount comes up read-only.
    if any(d.get("fstype") in NTFS_FSTYPES for d, _, _ in proposed):
        print("\n    NOTE: NTFS volumes mount read-only if Windows left them dirty via")
        print("    Fast Startup. If a mount below is read-only, boot Windows, run")
        print("    `powercfg /h off` as Administrator, reboot fully, and retry.")

    if not args.execute:
        print("\nRe-run with --execute to write these entries.")
        return 0

    # ---- apply ----
    backup = FSTAB.with_suffix(f".bak-{time.strftime('%Y%m%d-%H%M%S')}")
    try:
        run(["sudo", "cp", str(FSTAB), str(backup)])
        print(f"\n    backed up /etc/fstab -> {backup}")
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: could not back up /etc/fstab: {exc}", file=sys.stderr)
        return 1

    block = ["", "# added by will/bootstrap/mount_drives.py"]
    for dev, mountpoint, line in proposed:
        try:
            run(["sudo", "mkdir", "-p", mountpoint])
        except subprocess.CalledProcessError as exc:
            print(f"ERROR: mkdir {mountpoint}: {exc}", file=sys.stderr)
            return 1
        block.append(line)

    new_text = existing.rstrip("\n") + "\n" + "\n".join(block) + "\n"
    try:
        subprocess.run(["sudo", "tee", str(FSTAB)], input=new_text, text=True,
                       check=True, capture_output=True)
        print("    wrote /etc/fstab")
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: writing /etc/fstab: {exc}", file=sys.stderr)
        return 1

    verify = subprocess.run(["findmnt", "--verify"], capture_output=True, text=True)
    print("\n==> findmnt --verify")
    print(verify.stdout or "(no output)")
    if verify.returncode != 0:
        print(verify.stderr, file=sys.stderr)
        print(f"\n*** fstab failed verification. Restore with:", file=sys.stderr)
        print(f"      sudo cp {backup} /etc/fstab", file=sys.stderr)
        return 1

    run(["sudo", "systemctl", "daemon-reload"], check=False)
    mount_res = subprocess.run(["sudo", "mount", "-a"], capture_output=True, text=True)
    if mount_res.returncode != 0:
        print(f"\n!! mount -a reported: {mount_res.stderr.strip()}", file=sys.stderr)

    print("\n==> Result")
    failures = 0
    for _, mountpoint, _ in proposed:
        src = out(["findmnt", "-n", "-o", "SOURCE,FSTYPE,OPTIONS", mountpoint])
        if src:
            ro = ",ro," in f",{src.split()[-1]}," if len(src.split()) >= 3 else False
            print(f"    OK {mountpoint}: {src}")
            if ro:
                print("       ^ READ-ONLY — almost certainly a dirty NTFS volume. "
                      "See the Fast Startup note above.")
        else:
            print(f"    !! {mountpoint}: not mounted")
            failures += 1

    print("\nYour repos should now be at, e.g.:")
    ws = plan.get("Data", "/workspace")
    print(f"    cd {ws}/_code/will")
    print(f"\nIf anything looks wrong, restore the previous fstab:")
    print(f"    sudo cp {backup} /etc/fstab && sudo systemctl daemon-reload")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

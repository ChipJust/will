# Bootstrap — workstation setup

Three Python tools, run in order on a fresh machine. All three are **dry-run by
default** and print exactly what they would do; nothing changes until you pass
`--execute`.

| Script | Purpose | When |
|---|---|---|
| `mount_drives.py` | persistent `/etc/fstab` mounts for the carried-over drives | **first** — nothing else works until the drives are mounted |
| `bootstrap.py` | git, gh, Node, uv, Claude Code, GitHub auth, git config, adopt/clone repos, `uv sync`, plugins | after the drives are up |
| `harden.py` | unattended-upgrades, UFW default-deny, key-only SSH, Tailscale check, posture audit | day one, at the console |
| `restore.py` | copy staged Windows data off the old NTFS drive into `$HOME` | once `/srv/nas` is mounted |

## Before you wipe Windows

**Turn off Fast Startup.** Measured ON on the source machine 2026-10-07. A
Windows "shut down" with it enabled is a hybrid hibernate that leaves every NTFS
volume flagged dirty, and `ntfs3` then refuses a read-write mount — so
`/workspace` and `/srv/nas` come up read-only and the staged 63.85 GB on E: is
unwritable. As Administrator:

```
powercfg /h off
```

then reboot. (A `Restart` also bypasses Fast Startup, but `powercfg /h off` is
the reliable fix.)

## Usage

### Linux — fresh machine

```bash
bash setup.sh                                  # stage 0: git + python3 only
python3 bootstrap/bootstrap.py                 # preview
python3 bootstrap/bootstrap.py --execute       # apply, clones repos from GitHub
source ~/.bashrc                               # pick up uv + claude on PATH
```

### Linux — migration (the 2026-10 desktop-homelab case)

The repo drive came across from the old machine, so **there is nothing to
clone.** But a fresh install mounts only root/EFI/swap — the carried-over drives
are unmounted partitions until you say otherwise. Mount them first:

```bash
python3 bootstrap/mount_drives.py              # preview
sudo -v && python3 bootstrap/mount_drives.py --execute
```

That writes `/etc/fstab` entries for `Data -> /workspace`,
`Old Data -> /srv/nas`, `Old C -> /srv/media`, backs up the old fstab, runs
`findmnt --verify` before committing, and gives every entry `nofail` so a
missing or dirty drive can never block a boot. Then:

```bash
cd /workspace/_code/will
bash setup.sh
python3 bootstrap/bootstrap.py --workspace /workspace/_code              # preview
python3 bootstrap/bootstrap.py --execute --workspace /workspace/_code
source ~/.bashrc
```

Existing checkouts are adopted, not re-cloned. Cloning a second copy would be
worse than redundant — you would work in fresh clones while the real history,
local branches and uncommitted work sat on the other mount.

Adoption fixes three things that otherwise bite on a carried-over NTFS volume:

- `safe.directory` — git refuses repos whose ownership does not match the local
  uid ("dubious ownership") and will not run at all without this.
- `core.fileMode false` — NTFS has no exec bit, so git reports a mode change on
  essentially every file and `git status` becomes unreadable.
- Windows-built `.venv` — contains `Scripts/*.exe` rather than `bin/`. `uv` will
  not repair it in place, so it is removed before `uv sync` rebuilds it. As of
  2026-10-07 this affects `health`, `home`, `money`, `spatium`, `will`, `writing`.

### Then, on either path

```bash
python3 bootstrap/harden.py                    # preview
python3 bootstrap/harden.py --execute          # apply (run at the physical console)

python3 bootstrap/restore.py --source /srv/nas/_migration
python3 bootstrap/restore.py --source /srv/nas/_migration --execute --only home
```

### Windows

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\bootstrap\setup.ps1
```

`setup.ps1` is unchanged and still the Windows path. The Python tools target
Linux.

## Why Python replaced `bootstrap/setup.sh`

The old shell engine was removed in favour of `bootstrap.py`. It had four
problems worth remembering, since they are the kind of thing that recurs:

1. **`curl | bash` three times** — NodeSource, nvm, and the uv installer were
   piped straight into a shell. That directly contradicts the security posture
   recorded in `projects/desktop-homelab/STATUS.md` ("install from apt/signed
   vendor repos only"). Node now comes from the Ubuntu archive and uv from
   pipx. The one remaining `curl` fetches GitHub's apt *signing key*, which apt
   then uses to verify packages — a signed repo, not an unsigned script.
2. **Two Node strategies in one repo** — NodeSource in the root `setup.sh`, nvm
   in `bootstrap/setup.sh`.
3. **An ordering bug** — `SETUP.md` step 2 told the setup agent to run
   `gh auth status`, but the root `setup.sh` never installed `gh`.
4. **Cascading failure** — `set -euo pipefail` meant one unclonable repo aborted
   the whole run. `spatium` is local-only and not on GitHub, so this would have
   fired on the first real use. Each step is now independent and the summary
   reports what failed.

`setup.sh` survives as stage 0 only, because something has to run before Python
is guaranteed. It installs git and python3, then hands off.

## Dependencies

`bootstrap.py` uses **stdlib only** — it has to work before `uv` exists. Do not
add third-party imports to it. The same applies to `harden.py` and `restore.py`
so they stay runnable on a half-built system.

## Post-setup checklist

- [ ] `source ~/.bashrc` or open a new terminal
- [ ] Verify `claude` launches and plugins loaded (restart Claude Code after plugin install)
- [ ] `gh auth setup-git` ran — check `git config --global credential.helper`
- [ ] Tailscale: install from the apt repo for this release, then `sudo tailscale up`
- [ ] Verify a key-based SSH login *before* closing the console session
- [ ] ADR 0006 Phase B obligation: `gocryptfs`/`fscrypt` over the sensitive `/srv/nas` trees
- [ ] Still open in STATUS.md: a backup destination for irreplaceable family data

## Adding a step

Add it to the relevant phase function in `bootstrap.py` and make it idempotent —
check for the thing before installing it, and record `skip` when it is already
there. Every step must be safe to re-run.

# Bootstrap — workstation setup

Three Python tools, run in order on a fresh machine. All three are **dry-run by
default** and print exactly what they would do; nothing changes until you pass
`--execute`.

| Script | Purpose | When |
|---|---|---|
| `bootstrap.py` | git, gh, Node, uv, Claude Code, GitHub auth, git config, clone repos, `uv sync`, plugins | first, after `setup.sh` |
| `harden.py` | unattended-upgrades, UFW default-deny, key-only SSH, Tailscale check, posture audit | day one, at the console |
| `restore.py` | copy staged Windows data off the old NTFS drive into `$HOME` | once the old drive is mounted |

## Usage

### Linux

```bash
bash setup.sh                                  # stage 0: git + python3 only
python3 bootstrap/bootstrap.py                 # preview
python3 bootstrap/bootstrap.py --execute       # apply
source ~/.bashrc                               # pick up uv + claude on PATH

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

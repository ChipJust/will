---
name: commit-push
description: Stage files, commit, and push using the approved commit_push.py tool. Use this whenever you would otherwise chain `git add → git commit → git push`. Replaces the four-popup git chain with one pre-approved CLI call. The tool refuses dangerous patterns (secrets, force-flags, directories, detached HEAD, empty diff).
version: 1.0.0
---

# Skill: commit-push

When you would otherwise chain `git -C <repo> add <files>` → `git -C <repo> commit -m "..."` → `git -C <repo> push`, call this tool instead. It does the same operations behind a single pre-approved CLI, eliminating popups and centralizing safety checks.

## Usage

```
uv run python D:/_code/will/tools/commit_push.py <repo> <file1> [<file2>...] -m "<message>" [--no-push] [--allow-empty]
```

Arguments:
- `<repo>` — absolute path to the repo (e.g. `D:/_code/money`)
- `<file>` — files to stage; either repo-relative paths or absolute paths inside the repo. Multiple files accepted.
- `-m <message>` — commit message; multiline supported via bash heredoc.
- `--no-push` — commit only, do not push.
- `--allow-empty` — allow staging that produced no diff (rarely needed).

## When to use

- Always, for any commit you make on Chip's behalf.
- Replace this 3-call chain:
  ```
  git -C <repo> add <files>
  git -C <repo> commit -m "..."
  git -C <repo> push
  ```
  with:
  ```
  uv run python D:/_code/will/tools/commit_push.py <repo> <files> -m "..."
  ```

## When NOT to use

- For `git mv`, `git rm`, `git stash`, branch operations — those are not committed via this tool.
- For amending an existing commit (the tool refuses; per CLAUDE.md, prefer new commits).
- When you need to commit without pushing, use `--no-push`.

## Multiline messages (bash heredoc)

```bash
uv run python D:/_code/will/tools/commit_push.py D:/_code/money tools/foo.py -m "$(cat <<'EOF'
Subject line

Body paragraph here.

- Bullet
- Bullet
EOF
)"
```

The single-quoted heredoc (`'EOF'`) prevents shell expansion inside the message body — use it whenever the message contains `$`, backticks, or other shell metacharacters.

## What the tool refuses

- Files matching secret patterns: `.env*`, `*.pem`, `*.key`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `credentials*.json`, `secrets.{yaml,yml,json,toml}`
- Files outside the specified repo
- Files that don't exist
- Directories (pass specific files instead)
- Empty file list, empty message, empty staged diff (unless `--allow-empty`)
- Detached HEAD

These guardrails mean the tool can be pre-approved at the user-global tier (`Bash(uv run python D:/_code/will/tools/:*)`) without losing control over what gets committed.

## Output

The tool prints:
- Repo and branch
- Files staged (one per line)
- Staged diff stat
- Commit hash
- Push result

If anything fails before commit, it exits non-zero and does not push. If commit succeeds but push fails, the commit is preserved locally.

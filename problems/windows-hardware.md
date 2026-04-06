# Problem: Windows Does Not Support Target Hardware

**Logged:** 2026-04-06
**Status:** Open
**Affects:** All repos (portability risk)

## Description

The current development machine runs Windows 10 Pro. The target hardware Chip wants
to use is not supported by Windows. This creates a platform migration risk — at some
point the machine will need to move to Linux (or macOS) to support the hardware.

## Impact

- All tooling is currently written and tested on Windows (bash via Git Bash, paths
  with forward slashes, `cp1252` encoding gotchas)
- The UTF-8 encoding fix needed in `health/tools/extract/from_html.py` and
  `health/tools/ingest.py` (discovered 2026-04-06) is a Windows-specific issue
- TinyTeX installed via `pytinytex` may need reinstall on new OS
- `~/.claude/` directory structure and paths are Windows-specific

## What "Target Hardware" Means

*(Fill in: what hardware specifically requires Linux/macOS?)*

## Resolution Path

1. Identify the target OS (Linux distro vs. macOS)
2. Update portability checklist in `will/PLAN.md`
3. Audit all repos for Windows-specific assumptions (paths, encoding, shebangs)
4. Test ingest and convert tooling on target OS before migrating
5. Migrate `~/.claude/` directory (plugins, memory, settings)

## Notes

- The `will/PLAN.md` new-machine checklist should be completed before migration
- Encoding issues are the most likely class of platform-specific bugs; grep for
  `cp1252`, hardcoded `\`, and `sys.stdout` assumptions across all tools

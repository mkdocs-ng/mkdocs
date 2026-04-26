---
name: release
description: Prepare a new MkDocs-NG release by updating the version, release notes date, and running pre-release checks. Use when the user asks to start or prepare a release, cut a release, or update version numbers.
---

# Release Preparation

## Overview

Prepare the repository for a new MkDocs-NG release by updating the version string and release notes date.

## Workflow

1. **Determine the version.** Ask the user for the target version (e.g., `1.7.2`), or infer it from the `(Unreleased)` section in `docs/about/release-notes.md`.

2. **Update `mkdocs/__init__.py`.** Change `__version__` to the new version:

   ```diff
   -__version__ = "1.7.1"
   +__version__ = "1.7.2"
   ```

3. **Update `docs/about/release-notes.md`.** Replace `(Unreleased)` with today's date in `YYYY-MM-DD` format for the target version heading:

   ```diff
   -## Version 1.7.2 (Unreleased)
   +## Version 1.7.2 (2026-04-27)
   ```

   Use the current date. You can obtain it with:

   ```bash
   date +%Y-%m-%d
   ```

4. **Run pre-commit checks** to ensure everything passes:

   ```bash
   uvx prek run -a
   ```

   If checks fail, fix the reported issues and rerun until clean.

5. **Verify the changes** are correct:

   ```bash
   git diff
   ```

## Files Modified

| File | Change |
|------|--------|
| `mkdocs/__init__.py` | `__version__` string |
| `docs/about/release-notes.md` | Date in the target version heading |

No other files carry a hard-coded version. `pyproject.toml` reads the version dynamically from `mkdocs/__init__.py`.

## Notes

- Do not commit the changes automatically; let the user decide when to commit.
- The `pyproject.toml` uses `dynamic = ["version"]` with `tool.hatch.version.path = "mkdocs/__init__.py"`, so only `__init__.py` needs updating.
- After completing the release preparation, the user should create a git tag (e.g., `git tag 1.7.2`) and push it to trigger the PyPI publish workflow.

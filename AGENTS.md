# Agent Development Guide

This file gives AI coding agents repository-specific instructions for working on MkDocs NG. Follow the public contributor guidance in `CONTRIBUTING.md` first, then use these notes for agent workflow details.

## Communication

* Keep updates concise, technical, and specific to the current task.
* State which checks were run and any checks that could not be run.
* Do not invent issue numbers, changelog entries, or release-note policy. Use the issue, PR, or maintainer instruction in the current task.

## Git Workflow

* Check `git status --short --branch` before editing, before staging, and before committing.
* Work on one logical change per branch and pull request.
* Stage only files changed for the current task. Use explicit paths with `git add`.
* Do not use destructive commands such as `git reset --hard`, `git checkout .`, or `git clean -fd` unless the user explicitly asks for them.
* Do not rewrite branch history or force-push unless the user explicitly asks for it.
* If unrelated local changes are present, leave them untouched.

## Project Layout

* Core package code lives under `mkdocs/`.
* Tests live under `mkdocs/tests/` and use Python's `unittest` framework.
* User documentation lives under `docs/`.
* Built-in themes and their translation templates live under `mkdocs/themes/`.
* Project configuration, test commands, lint rules, and Hatch environments are in `pyproject.toml`.
* Repository hooks are configured in `.pre-commit-config.yaml`.

## Development Commands

Use Hatch when it is available:

```bash
hatch run test:test
hatch run integration:test
hatch run types:check
pre-commit run --all-files
```

For focused local validation, it is acceptable to run a specific `unittest` target:

```bash
python -m unittest mkdocs.tests.build_tests.BuildTests.test_example
```

If the local environment uses the repository virtualenv, prefer:

```bash
./.venv/bin/python -m unittest mkdocs.tests.build_tests.BuildTests.test_example
./.venv/bin/python -m mkdocs build --strict
```

When changing documentation, preview with:

```bash
hatch run docs:serve
```

## Testing Rules

* Add or update tests for behavior changes, regressions, and bug fixes.
* Run the narrowest relevant test first, then broader checks when the change has wider impact.
* If a command fails because of environment or dependency resolution, report the exact command and failure reason.
* Do not treat a successful documentation build as a substitute for code tests when Python behavior changed.

## Code Style

* Match existing style and local helper APIs before adding new abstractions.
* Keep changes narrowly scoped to the requested behavior.
* Use Ruff formatting/import ordering through the configured hooks.
* Prefer clear, typed Python code. Avoid broad exception handling unless the surrounding code already uses that pattern.
* Add comments only when they explain non-obvious behavior.

## Documentation And Release Notes

* Documentation changes belong under `docs/` unless the task is only internal repository guidance.
* Follow the release-note policy in `CONTRIBUTING.md`: release notes are usually maintainer-written.
* If the user or maintainer explicitly requests a release-note entry, add it to the current unreleased section in `docs/about/release-notes.md`.
* Keep release-note entries short and user-facing, with issue or PR references when known.

## Pull Requests

* Keep the PR title specific and action-oriented.
* In the PR body, include what changed, why it changed, and validation performed.
* Link related issues with `Fixes`, `Closes`, or contextual references only when that relationship is correct.
* Use separate PRs for unrelated changes.

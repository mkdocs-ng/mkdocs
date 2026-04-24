# Development Rules

## Quality Gate

* Before every final commit, run `uvx prek run -a`.
* Pre-commit must pass before committing. If it fails, fix the reported issues and rerun `uvx prek run -a` until it passes.
* Do not use `git commit --no-verify` to bypass required checks.

## Git Safety

* Run `git status` before staging or committing.
* Stage only files changed for the current task, using explicit paths.
* Do not use `git add .` or `git add -A`, because they can include unrelated work.
* Do not run destructive commands such as `git reset --hard`, `git checkout .`, or `git clean -fd` unless the user explicitly asks for them.

## Project Notes

* When updating release notes, edit `docs/about/release-notes.md` and add entries to the latest version section near the top of the file.
* Keep release note entries user-facing and consistent with the surrounding section style.

# Development Rules

## Quality Gate

* Before every final commit, run `uvx prek run -a`.
* Pre-commit must pass before committing. If it fails, fix the reported issues and rerun `uvx prek run -a` until it passes.
* Do not use `git commit --no-verify` to bypass required checks.

## Git Safety

* Never git push directly to the `main` branch. Always create a pull request.
* Run `git status` before staging or committing.
* Stage only files changed for the current task, using explicit paths.
* Do not use `git add .` or `git add -A`, because they can include unrelated work.
* Do not run destructive commands such as `git reset --hard`, `git checkout .`, or `git clean -fd` unless the user explicitly asks for them.

## Referencing the Upstream Project

* Do not reference upstream `mkdocs/mkdocs` issues, discussions, or pull requests in commit messages, pull request titles/bodies, issue comments, or review comments. Bare references (`mkdocs/mkdocs#1234`) and full issue URLs both create visible cross-reference backlinks on the upstream tracker, and this project prefers to keep a low profile there.
* Instead, describe the problem being solved in your own words (symptom, root cause, fix). If context about upstream history is truly needed, keep it in local docs or code comments — never in GitHub-side content that generates a backlink.
* Do not post comments on the upstream tracker.
* Referencing this repository's own issues and pull requests (`#NN`) is fine and encouraged.

## Project Notes

* When updating release notes, edit `docs/about/release-notes.md` and add entries to the latest version section near the top of the file.
* Keep release note entries user-facing and consistent with the surrounding section style.

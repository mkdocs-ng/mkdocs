# Contributing to MkDocs NG

Thanks for wanting to contribute to MkDocs NG. This guide is intentionally
short; it exists to help contributors send focused, reviewable changes.

Use [GitHub Discussions] for questions and general help. Use [GitHub issues]
for bug reports and feature requests.

## The Main Rule

You must understand the code you contribute.

Using AI to help write code is fine. What is not fine is submitting code you do
not understand. If you cannot explain what your changes do, why they are needed,
and how they interact with the rest of the project, your PR may be closed.

If you use an AI coding agent, run it from the repository root so it can pick up
`AGENTS.md`, and review its output carefully before opening a PR.

## Reporting Issues

Please include enough detail for someone else to reproduce or understand the
problem:

* What you were trying to do.
* Your MkDocs version, Python version, platform, and relevant `mkdocs.yml`.
* What you expected to happen.
* What happened instead, including the full error message or traceback.
* Screenshots for visual or theme issues.

For large feature ideas, open a discussion or issue before starting the PR.

## Development Setup

Install [Hatch] to run the development environments:

```bash
pipx install hatch
```

Install [prek] or use it through `uvx` to run repository hooks:

```bash
uvx prek run -a
```

The hooks cover formatting, linting, spelling, YAML/TOML validation, Markdown
linting, and JavaScript linting.

## Useful Checks

Run the checks that match your change before opening a PR:

```bash
uvx prek run -a
hatch run test:test
hatch run integration:test
hatch run types:check
```

If you changed documentation, preview it locally:

```bash
hatch run docs:serve
```

Resolve documentation warnings before submitting documentation changes.

## Pull Requests

Keep PRs focused and easy to review. A PR should usually do one thing.

For changes that affect behavior, add or update tests. For user-facing changes,
update documentation when appropriate.

Do not force-push during review unless there is a clear reason. Review history
is easier to follow when updates are pushed as normal commits; PRs are typically
squash-merged.

If release notes are needed, update `docs/about/release-notes.md` in the latest
version section near the top of the file. Keep entries user-facing and
consistent with the surrounding style.

## Code of Conduct

Everyone interacting in MkDocs NG spaces is expected to follow the
[PyPA Code of Conduct].

[GitHub Discussions]: https://github.com/orgs/mkdocs-ng/discussions
[GitHub issues]: https://github.com/mkdocs-ng/mkdocs/issues
[Hatch]: https://hatch.pypa.io/
[prek]: https://github.com/j178/prek
[PyPA Code of Conduct]: https://www.pypa.io/en/latest/code-of-conduct/

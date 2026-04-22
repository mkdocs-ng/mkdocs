# Contributing to MkDocs

An introduction to contributing to the MkDocs project.

The MkDocs project welcomes contributions from developers and
users in the open source community. Contributions can be made in a number of
ways, a few examples are:

- Code patches via pull requests
- Documentation improvements
- Bug reports and patch reviews

For information about available communication channels please refer to the
[README](https://github.com/mkdocs-ng/mkdocs#readme) file in our
GitHub repository.

## Reporting an Issue

Please include as much detail as you can. Let us know your platform and MkDocs
version. If the problem is visual (for example a theme or design issue), please
add a screenshot. If you get an error, please include the full error message and
traceback.

It is particularly helpful if an issue report touches on all of these aspects:

1.  What are you trying to achieve?

2.  What is your `mkdocs.yml` configuration (+ other relevant files)? Preferably reduced to the minimal reproducible example.

3.  What did you expect to happen when applying this setup?

4.  What happened instead and how didn't it match your expectation?

## Trying out the Development Version

If you want to just install and try out the latest development version of
MkDocs (in case it already contains a fix for your issue),
you can do so with the following command. This can be useful if you
want to provide feedback for a new feature or want to confirm if a bug you
have encountered is fixed in the git master. It is **strongly** recommended
that you do this within a [virtualenv].

```bash
pip install git+https://github.com/mkdocs-ng/mkdocs.git
```

## Installing for Development

Note that for development you can just use [Hatch] directly as described below. If you wish to install a local clone of MkDocs anyway, you can run `pip install --editable .`. It is **strongly** recommended that you do this within a [virtualenv].

## Installing development tools

The project provides two equivalent ways to run development tasks. You only need **one** of them.

### Option A — Nox (recommended for contributors)

[Nox] is a simple command runner that manages its own virtualenvs. Install it once:

```bash
pipx install nox   # recommended (isolated)
# or
pip install nox
```

All available sessions can be listed with:

```bash
nox -l
```

Quick reference:

| Task | Command |
|------|---------|
| Unit tests | `nox -s tests` |
| Unit tests + coverage | `nox -s coverage` |
| Integration tests | `nox -s integration` |
| Ruff lint | `nox -s lint` |
| Auto-fix formatting | `nox -s format` |
| Check formatting only | `nox -s format_check` |
| Type check (mypy) | `nox -s typing` |
| Spell check | `nox -s spelling` |
| Markdown lint | `nox -s markdown` |
| JS lint | `nox -s js` |
| Build docs | `nox -s docs` |
| Serve docs locally | `nox -s docs_serve` |

Run the most common checks in one go:

```bash
nox  # runs: tests, lint, typing
```

### Option B — Hatch

[Hatch] manages dependencies in a virtualenv that is created on the fly and is also a command runner.

[Install it][install Hatch] with **`pipx install hatch`** (after [installing `pipx`]), or just `pip install hatch`.

## Running all checks

With **nox**:

```bash
nox -s tests integration lint format_check typing spelling
```

With **hatch**:

```bash
hatch run all
```

All checks need to pass.

### Running tests

To run the test suite for MkDocs:

```bash
# nox
nox -s tests
nox -s integration

# hatch
hatch run test:test
hatch run integration:test
```

It will attempt to run the tests against all of the Python versions we
support. So don't be concerned if you are missing some. The rest
will be verified by [GitHub Actions] when you submit a pull request.

### Python code style

Python code within MkDocs' code base is formatted using [Black] and [Isort] and lint-checked using [Ruff], all of which are configured in `pyproject.toml`.

You can automatically check and format the code:

```bash
# nox
nox -s format

# hatch
hatch run style:fix
```

The code is also type-checked using [mypy]:

```bash
# nox
nox -s typing

# hatch
hatch run types:check
```

### Other style checks

There are several other checks, such as spelling and JS style:

```bash
# nox
nox -s spelling markdown js

# hatch
hatch run lint:check
```

### Documentation of MkDocs itself

After making edits to files under the `docs/` dir, you can preview the site locally:

```bash
# nox
nox -s docs_serve

# hatch
hatch run docs:serve
```

Note that any 'WARNING' should be resolved before submitting a contribution.

Documentation files are also checked by markdownlint, so you should run this as well:

```bash
# nox
nox -s markdown

# hatch
hatch run lint:check
```

If you add a new plugin to mkdocs.yml, you don't need to add it to any "requirements" file, because that is managed automatically.

> INFO: If you don't want to use Hatch, for documentation you can install dependencies into a virtualenv (with `.venv` being the virtualenv directory):
>
> ```bash
> .venv/bin/pip install --editable .
> .venv/bin/pip install $(mkdocs get-deps)  # Additional dependencies from mkdocs.yml plugins/themes.
> ```

## Translating themes

To localize a theme to your favorite language, follow the guide on [Translating Themes]. We welcome translation pull requests!

## Submitting Pull Requests

If you're considering a large code contribution to MkDocs, please prefer to
open an issue first to get early feedback on the idea.

Once you think the code is ready to be reviewed, push
it to your fork and send a pull request. For a change to be accepted it will
most likely need to have tests and documentation if it is a new feature.

When working with a pull request branch:
Unless otherwise agreed, prefer `commit` over `amend`, and `merge` over `rebase`. Avoid force-pushes, otherwise review history is much harder to navigate. For the end result, the "unclean" history is fine because most pull requests are squash-merged on GitHub.

Do *not* add to *release-notes.md*, this will be written later.

### Submitting changes to the builtin themes

When installed with `i18n` support (`pip install 'mkdocs[i18n]'`), MkDocs allows
themes to support being translated into various languages (referred to as
locales) if they respect [Jinja's i18n extension] by wrapping text placeholders
with `{% trans %}` and `{% endtrans %}` tags.

Each time a translatable text placeholder is added, removed or changed in a
theme template, the theme's Portable Object Template (`pot`) file needs to be
updated by running the `extract_messages` command. To update the
`pot` file for both built-in themes, run these commands:

```bash
pybabel extract --project=MkDocs --copyright-holder=MkDocs --msgid-bugs-address='https://github.com/mkdocs-ng/mkdocs/issues' --no-wrap --version="$(hatch version)" --mapping-file mkdocs/themes/babel.cfg --output-file mkdocs/themes/mkdocs/messages.pot mkdocs/themes/mkdocs
pybabel extract --project=MkDocs --copyright-holder=MkDocs --msgid-bugs-address='https://github.com/mkdocs-ng/mkdocs/issues' --no-wrap --version="$(hatch version)" --mapping-file mkdocs/themes/babel.cfg --output-file mkdocs/themes/readthedocs/messages.pot mkdocs/themes/readthedocs
```

The updated `pot` file should be included in a PR with the updated template.
The updated `pot` file will allow translation contributors to propose the
translations needed for their preferred language. See the guide on [Translating
Themes] for details.

NOTE:
Contributors are not expected to provide translations with their changes to
a theme's templates. However, they are expected to include an updated `pot`
file so that everything is ready for translators to do their job.

## Code of Conduct

Everyone interacting in the MkDocs project's codebases, issue trackers, chat
rooms, and mailing lists is expected to follow the [PyPA Code of Conduct].

[virtualenv]: https://virtualenv.pypa.io/en/latest/user_guide.html
[Nox]: https://nox.thea.codes/
[Hatch]: https://hatch.pypa.io/
[install Hatch]: https://hatch.pypa.io/latest/install/#pip
[installing `pipx`]: https://pypa.github.io/pipx/installation/
[GitHub Actions]: https://docs.github.com/actions
[PyPA Code of Conduct]: https://www.pypa.io/en/latest/code-of-conduct/
[Translating Themes]: https://mkdocs-ng.github.io/mkdocs/dev-guide/translations/
[Jinja's i18n extension]: https://jinja.palletsprojects.com/en/latest/extensions/#i18n-extension
[Ruff]: https://docs.astral.sh/ruff/
[Black]: https://black.readthedocs.io/
[Isort]: https://pycqa.github.io/isort/
[mypy]: https://mypy-lang.org/

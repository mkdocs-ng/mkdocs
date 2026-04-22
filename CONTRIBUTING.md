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

The project uses [Nox] as its task runner. Install it once:

```bash
pipx install nox   # recommended (isolated)
# or
pip install nox
```

Run the most common checks before submitting a PR:

```bash
nox  # runs: tests, lint, typing
```

List all available tasks with `nox -l`, then run any one by name, e.g. `nox -s format`.

## Running checks

### Tests

```bash
nox -s tests
nox -s integration
```

### Code style

```bash
nox -s format    # auto-fix (isort + black + ruff)
nox -s lint      # check only (ruff)
nox -s typing    # mypy
```

### Documentation

```bash
nox -s docs        # build
nox -s docs-serve  # local preview
```

Note that any 'WARNING' should be resolved before submitting a contribution. Documentation files are also checked by markdownlint (`nox -s markdown`).

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
[PyPA Code of Conduct]: https://www.pypa.io/en/latest/code-of-conduct/
[Translating Themes]: https://mkdocs-ng.github.io/mkdocs/dev-guide/translations/
[Jinja's i18n extension]: https://jinja.palletsprojects.com/en/latest/extensions/#i18n-extension

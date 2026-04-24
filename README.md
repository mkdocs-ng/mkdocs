# MkDocs

> *Project documentation with Markdown*

[![PyPI Version][pypi-v-image]][pypi-v-link]
[![Build Status][GHAction-image]][GHAction-link]
[![Coverage Status][codecov-image]][codecov-link]

MkDocs is a **fast**, **simple**, and **downright gorgeous** static site
generator that's geared towards building project documentation. Documentation
source files are written in Markdown and configured with a single YAML
configuration file. It is designed to be easy to use and can be extended with
third-party themes, plugins, and Markdown extensions.

> [!NOTE]
> **mkdocs** is a fork of [mkdocs/mkdocs], actively maintained since 1.7.0
> and published as `mkdocs-ng` while preserving the `mkdocs` CLI.
>
> It includes support for Python 3.13 and 3.14, restores `mkdocs serve --livereload`,
> improves strict link and anchor validation, ensures reliable cleanup on `SIGTERM`,
> removes the unmaintained `mergedeep` dependency, and modernizes CI, dependencies,
> release workflows and much [more].
>
> The project is under active maintenance.

Please see the [Documentation][mkdocs] for an introductory tutorial and a full user guide.

## Features

- Build static HTML files from Markdown files.
- Use Plugins and Markdown Extensions to enhance MkDocs.
- Use the built-in themes, third-party themes, or create your own.
- Publish your documentation anywhere that static files can be served.
- Much more!

## Support

If you need help with MkDocs:

- Use **[Discussions]** for questions and general help.
- To report a bug or make a feature request, open an **[Issue]** on GitHub.

We may only provide support for core MkDocs features. Questions about
third-party themes, plugins, or extensions should usually go to those projects
first, but they are still welcome in [Discussions].

## Links

- [Official Documentation][mkdocs]
- [Latest Release Notes][release-notes]
- [Catalog of third-party plugins, themes and recipes][catalog]

## Contributing to MkDocs

The MkDocs project welcomes and depends on contributions from developers and
users in the open source community. Please see the [Contributing Guide] for
information on how you can help.

## Code of Conduct

Everyone interacting in the MkDocs project's codebases, issue trackers, and
discussion forums are expected to follow the [PyPA Code of Conduct].

<!-- Badges -->
[codecov-image]: https://codecov.io/github/mkdocs-ng/mkdocs/coverage.svg?branch=main
[codecov-link]: https://codecov.io/github/mkdocs-ng/mkdocs?branch=main
[pypi-v-image]: https://img.shields.io/pypi/v/mkdocs-ng.svg
[pypi-v-link]: https://pypi.org/project/mkdocs-ng/
[GHAction-image]: https://github.com/mkdocs-ng/mkdocs/actions/workflows/ci.yml/badge.svg
[GHAction-link]: https://github.com/mkdocs-ng/mkdocs/actions/workflows/ci.yml
<!-- Links -->
[mkdocs]: https://mkdocs-ng.github.io/mkdocs/
[mkdocs/mkdocs]: https://github.com/mkdocs-ng/mkdocs
[more]: https://github.com/mkdocs-ng/mkdocs/pulls?page=1&q=is%3Apr+is%3Aclosed+is%3Amerged
[Issue]: https://github.com/mkdocs-ng/mkdocs/issues
[Discussions]: https://github.com/orgs/mkdocs-ng/discussions
[release-notes]: https://mkdocs-ng.github.io/mkdocs/about/release-notes/
[Contributing Guide]: https://mkdocs-ng.github.io/mkdocs/about/contributing/
[PyPA Code of Conduct]: https://www.pypa.io/en/latest/code-of-conduct/
[catalog]: https://github.com/mkdocs-ng/catalog

## License

[BSD-2-Clause](https://github.com/mkdocs-ng/mkdocs/blob/main/LICENSE)

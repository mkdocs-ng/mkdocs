<p align="center">
  <a href="https://mkdocs-ng.org/">
    <img src="https://raw.githubusercontent.com/mkdocs-ng/mkdocs/main/docs/img/social.png" width="100%" alt="MkDocs NG. Write Markdown. Ship docs. The maintained MkDocs that keeps your plugins working.">
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/mkdocs-ng/"><img src="https://img.shields.io/pypi/v/mkdocs-ng.svg?style=flat-square&label=pypi&labelColor=011c46&color=0061fe" alt="PyPI version"></a>
  <a href="https://pypi.org/project/mkdocs-ng/"><img src="https://img.shields.io/pypi/pyversions/mkdocs-ng.svg?style=flat-square&labelColor=011c46&color=0061fe" alt="Python versions"></a>
  <a href="https://mkdocs-ng.org/user-guide/migrating/#plugins-and-themes"><img src="https://img.shields.io/github/actions/workflow/status/mkdocs-ng/mkdocs/compat.yml?branch=main&style=flat-square&labelColor=011c46&label=plugin%20compatibility" alt="Plugin compatibility"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/mkdocs-ng/mkdocs"><img src="https://img.shields.io/ossf-scorecard/github.com/mkdocs-ng/mkdocs?style=flat-square&labelColor=011c46&label=openssf%20scorecard" alt="OpenSSF Scorecard"></a>
  <a href="https://github.com/mkdocs-ng/mkdocs/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/mkdocs-ng.svg?style=flat-square&labelColor=011c46&color=0061fe" alt="License"></a>
</p>

<p align="center">
  <a href="https://mkdocs-ng.org/">Documentation</a> ·
  <a href="https://mkdocs-ng.org/user-guide/migrating/">Switching from MkDocs</a> ·
  <a href="https://mkdocs-ng.org/about/release-notes/">Release notes</a> ·
  <a href="https://catalog.mkdocs-ng.org/">Plugin catalog</a>
</p>

**MkDocs NG** is the maintained fork of [MkDocs][mkdocs/mkdocs] 1.x. Upstream
MkDocs has had no 1.x release since August 2024, and its 2.0 rewrite can't
build existing sites. MkDocs NG keeps the `mkdocs` command, `mkdocs.yml`,
plugins and themes working, with bug, security and compatibility fixes until at
least 2028-12-31. See [Is MkDocs still maintained?][is-maintained] and
[MkDocs alternatives compared][comparison].

One `mkdocs.yml` turns a folder of Markdown files into a fast, static
documentation site you can host anywhere. Pick a built-in theme,
[Sumi](https://sumi.mkdocs-ng.org/) or any of the hundreds of third-party
themes, plugins and Markdown extensions in the
[catalog](https://catalog.mkdocs-ng.org/).

<p align="center">
  <a href="https://mkdocs-ng.org/about/comparison/#build-speed">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mkdocs-ng/mkdocs/main/docs/img/build-speed-dark.svg">
      <img src="https://raw.githubusercontent.com/mkdocs-ng/mkdocs/main/docs/img/build-speed.svg" width="720" alt="Clean build of a 1,000-page site: MkDocs NG with Material 11.1 s, Zensical 15.9 s, Sphinx with 4 processes 23.5 s, ProperDocs with Material 32.1 s, Starlight 32.9 s, MkDocs 1.6.1 with Material 34.2 s, VitePress 85.4 s, Docusaurus 106.6 s">
    </picture>
  </a>
</p>

<p align="center">
  <i>Clean build of the same 1,000-page site. Zensical is faster when it reuses its cache and when <code>serve</code> shows an edit.
  <br>
  <a href="https://mkdocs-ng.org/about/comparison/#build-speed">How we measured</a></i>
</p>

> [!NOTE]
> **MkDocs NG** is published on PyPI as `mkdocs-ng` while keeping the `mkdocs`
> command, imports and configuration unchanged — a drop-in replacement.
>
> Highlights beyond the last upstream release: Python 3.10–3.15 support,
> built-in `llms.txt` and per-page Markdown output for LLMs and coding agents,
> search that finds programming keywords like `while` and `for`, faster
> builds with smaller site output, a stable Python API (`mkdocs.build()` /
> `mkdocs.serve()`), fully offline syntax highlighting with no CDNs or
> analytics, and many long-standing bug fixes — see
> [Fixed Upstream Issues][fixed-upstream] and the [release notes][release-notes],
> or browse [all merged changes][more].

Please see the [Documentation][mkdocs] for an introductory tutorial and a full user guide.

## Features

- Build static HTML files from Markdown files.
- Use Plugins and Markdown Extensions to enhance MkDocs.
- Use the built-in themes, third-party themes, or create your own.
- Publish your documentation anywhere that static files can be served.
- Much more!

## Installation

Install with pip:

```bash
pip install mkdocs-ng
```

Switching from `mkdocs`? Just install MkDocs NG — the command, imports and
configuration stay exactly the same:

```bash
pip install -U mkdocs-ng
```

Plugins and themes depend on the `mkdocs` package, so upstream MkDocs gets
installed alongside. That's fine: MkDocs NG installs its files separately and
always takes precedence, so leave the upstream package installed. See
[Plugins, themes and the `mkdocs` package][plugins-install] for details, and
[Switching to MkDocs NG][migrating] for what behaves differently from upstream
MkDocs.

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
- [Fixed Upstream Issues][fixed-upstream]
- [Switching to MkDocs NG][migrating]
- [Governance and how long 1.x is supported][governance]
- [Is MkDocs still maintained?][is-maintained]
- [MkDocs alternatives compared: MkDocs NG, MkDocs 2.0, ProperDocs and Zensical][comparison]
- [Catalog of third-party plugins, themes and recipes][catalog]
- [Sumi][sumi], a local-first documentation theme from the MkDocs NG project
- [MkDocs NG Material][ng-material], Material for MkDocs maintained for MkDocs NG

## Contributing to MkDocs

The MkDocs project welcomes and depends on contributions from developers and
users in the open source community. Please see the [Contributing Guide] for
information on how you can help.

## Code of Conduct

Everyone interacting in the MkDocs project's codebases, issue trackers, and
discussion forums are expected to follow the [PyPA Code of Conduct].

<!-- Links -->
[mkdocs]: https://mkdocs-ng.org/
[mkdocs/mkdocs]: https://github.com/mkdocs/mkdocs
[more]: https://github.com/mkdocs-ng/mkdocs/pulls?page=1&q=is%3Apr+is%3Aclosed+is%3Amerged
[Issue]: https://github.com/mkdocs-ng/mkdocs/issues
[Discussions]: https://github.com/orgs/mkdocs-ng/discussions
[release-notes]: https://mkdocs-ng.org/about/release-notes/
[fixed-upstream]: https://mkdocs-ng.org/about/fixed-upstream-issues/
[plugins-install]: https://mkdocs-ng.org/user-guide/installation/#plugins-themes-and-the-mkdocs-package
[migrating]: https://mkdocs-ng.org/user-guide/migrating/
[comparison]: https://mkdocs-ng.org/about/comparison/
[is-maintained]: https://mkdocs-ng.org/user-guide/is-mkdocs-still-maintained/
[governance]: https://mkdocs-ng.org/about/governance/
[Contributing Guide]: https://mkdocs-ng.org/about/contributing/
[PyPA Code of Conduct]: https://www.pypa.io/en/latest/code-of-conduct/
[catalog]: https://catalog.mkdocs-ng.org/
[sumi]: https://sumi.mkdocs-ng.org/
[ng-material]: https://material.mkdocs-ng.org/

## License

[BSD-2-Clause](https://github.com/mkdocs-ng/mkdocs/blob/main/LICENSE)

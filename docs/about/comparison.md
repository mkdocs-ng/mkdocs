# MkDocs NG and Its Alternatives

How MkDocs NG relates to the other tools that build MkDocs sites.

---

Since upstream MkDocs 1.x stopped being developed, several projects have
offered a way forward for existing MkDocs sites. This page compares them on
what matters when you already have a site: whether it keeps building
unchanged, and whether your plugins keep running.

Facts on this page were checked on 2026-11-01 against each project's PyPI
release history, documentation and source code; see [Sources](#sources).
Projects change quickly, so check their documentation for the current state.
If something here is wrong or out of date, please
[open an issue](https://github.com/mkdocs-ng/mkdocs/issues).

## At a glance

&nbsp; | MkDocs NG | MkDocs 1.6 | MkDocs 2.0 pre-releases | ProperDocs | Zensical
--- | --- | --- | --- | --- | ---
What it is | Maintained fork of MkDocs 1.x | Last upstream 1.x release | Upstream rewrite | Fork of MkDocs 1.6 | New generator by the Material for MkDocs team
Latest release | 1.10.0rc1 (2026-11-01) | 1.6.1 (2024-08-30) | 2.0.dev6 (2026-09-15) | 1.6.7 (2026-03-20) | 0.0.74 (2026-10-30)
PyPI package | `mkdocs-ng` | `mkdocs` | `mkdocs` (`--pre`) | `properdocs` | `zensical`
Command | `mkdocs` | `mkdocs` | `mkdocs` | `properdocs` | `zensical`
Configuration | `mkdocs.yml` | `mkdocs.yml` | None; refuses to run when `mkdocs.yml` exists | `properdocs.yml`, falls back to `mkdocs.yml` | `mkdocs.yml` or `zensical.toml`
Runs MkDocs plugins | Yes | Yes | No | Yes | No; reimplements about 30 popular ones
Runs MkDocs themes | Yes | Yes | No | Yes | No; its own theme supports Material for MkDocs settings
Python | 3.10+ | 3.8+ | 3.10+ | 3.9+ | 3.11+

## MkDocs 1.6

The last release of upstream MkDocs 1.x is 1.6.1, from August 2024. Sites and
plugins built for it keep working, but bugs reported since then stay unfixed,
and it declares support for Python 3.8 to 3.12 only. Plugins and themes keep
installing it as a dependency, which is why MkDocs NG installs alongside it
and takes precedence instead of replacing it. See
[Plugins, themes and the `mkdocs` package](../user-guide/installation.md#plugins-themes-and-the-mkdocs-package).

## MkDocs 2.0 pre-releases

Upstream MkDocs 2.0 is a rewrite, published as pre-releases of the `mkdocs`
package, so `pip install mkdocs` still installs 1.6.1 and only
`pip install --pre mkdocs` installs 2.0. As of 2.0.dev6 it builds a directory
of Markdown files with a single Jinja template (`templates/base.html`). It has
no configuration file, plugins or themes, and it stops with an error when it
finds a `mkdocs.yml`. Existing sites can't be built with it.

## ProperDocs

ProperDocs is a fork of MkDocs 1.6 with its own package, command and
configuration file name. It loads plugins and themes written for MkDocs, so
existing sites can move to it by running `properdocs` instead of `mkdocs`;
it also reads `mkdocs.yml`. Several plugins, including `mkdocs-redirects`,
`mkdocs-gen-files`, `mkdocs-literate-nav`, `mkdocs-section-index` and
`mkdocs-rss-plugin`, now depend on ProperDocs and print a warning suggesting
it when run by the `mkdocs` command. They keep working with MkDocs NG, which
turns that warning off.

## Zensical

Zensical is a new static site generator from the team behind Material for
MkDocs, which is in maintenance mode with critical fixes through 2027-05-05.
It reads existing `mkdocs.yml` files and supports Material for MkDocs
settings. It doesn't run MkDocs plugins: it reimplements about 30 popular
ones natively and ignores the configuration of the rest. `gh-deploy`,
`get-deps` and `hooks` aren't supported, and templates use MiniJinja instead
of Jinja. It is a good fit if your site uses Material for MkDocs and only
plugins it supports.

## MkDocs NG

MkDocs NG continues MkDocs 1.x: same command, same `mkdocs.yml`, same plugin
and theme APIs, so switching is a package change. On top of that it supports
current Python versions (3.10 to 3.15), fixes
[long-standing upstream bugs](fixed-upstream-issues.md), and adds features
such as `llms.txt` output for LLMs and coding agents, a stable Python API, and
built-in themes that load nothing from CDNs. Every change is tested by
building sites with around 30 popular plugins, themes and Markdown
extensions. See [Switching to MkDocs NG](../user-guide/migrating.md).

## Sources

*   PyPI release history:
    [mkdocs-ng](https://pypi.org/project/mkdocs-ng/#history),
    [mkdocs](https://pypi.org/project/mkdocs/#history),
    [properdocs](https://pypi.org/project/properdocs/#history),
    [zensical](https://pypi.org/project/zensical/#history).
*   MkDocs 2.0: the [package description](https://pypi.org/project/mkdocs/2.0.dev6/)
    and the source code of 2.0.dev6.
*   ProperDocs: [documentation](https://properdocs.org/) and the source code of
    1.6.7.
*   Zensical:
    [migrating from MkDocs](https://zensical.org/docs/compatibility/mkdocs/migration/),
    [MkDocs plugin support](https://zensical.org/docs/compatibility/mkdocs/plugins/).
*   Material for MkDocs maintenance:
    [upcoming changes](https://zensical.org/upcoming-changes/#material-for-mkdocs).

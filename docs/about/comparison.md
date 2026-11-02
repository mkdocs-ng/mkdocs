# MkDocs NG and Its Alternatives

How MkDocs NG relates to the other tools that build MkDocs sites.

---

Since upstream MkDocs 1.x stopped being developed, several projects have
offered a way forward for existing MkDocs sites. This page compares them on
what matters when you already have a site: whether it keeps building
unchanged, and whether your plugins keep running.

Facts on this page were checked on 2026-11-01 against each project's PyPI
release history, documentation and source code; see [Sources](#sources).
Build times were measured on 2026-11-02.
Projects change quickly, so check their documentation for the current state.
If something here is wrong or out of date, please
[open an issue](https://github.com/mkdocs-ng/mkdocs/issues).

## At a glance

&nbsp; | MkDocs NG | MkDocs 1.6 | MkDocs 2.0 pre-releases | ProperDocs | Zensical
--- | --- | --- | --- | --- | ---
What it is | Maintained fork of MkDocs 1.x | Last upstream 1.x release | Upstream rewrite | Fork of MkDocs 1.6 | New generator by the Material for MkDocs team
Latest release | 1.11.0rc1 (2026-11-03) | 1.6.1 (2024-08-30) | 2.0.dev6 (2026-09-15) | 1.6.7 (2026-03-20) | 0.0.74 (2026-10-30)
PyPI package | `mkdocs-ng` | `mkdocs` | `mkdocs` (`--pre`) | `properdocs` | `zensical`
Command | `mkdocs` | `mkdocs` | `mkdocs` | `properdocs` | `zensical`
Configuration | `mkdocs.yml` | `mkdocs.yml` | None; refuses to run when `mkdocs.yml` exists | `properdocs.yml`, falls back to `mkdocs.yml` | `mkdocs.yml` or `zensical.toml`
Runs MkDocs plugins | Yes | Yes | No | Yes | No; reimplements about 30 popular ones
Runs MkDocs themes | Yes | Yes | No | Yes | No; its own theme supports Material for MkDocs settings
Python | 3.10+ | 3.8+ | 3.10+ | 3.9+ | 3.11+
Build of a 1,000-page site | 9.3 s | 20.3 s | Can't build it | 19.9 s | 18.2 s; 6.4 s with its cache

See [Build speed](#build-speed) for how this was measured.

## Which one should I use?

*   **You have an MkDocs site and want it to keep building unchanged,
    plugins included:** MkDocs NG or ProperDocs. Both run MkDocs plugins and
    themes. With MkDocs NG the only change is the package name: the `mkdocs`
    command, `mkdocs.yml`, CI scripts and `.readthedocs.yaml` stay as they are.
    ProperDocs uses its own `properdocs` command.
*   **Your site uses Material for MkDocs, and only plugins that Zensical
    reimplements:** Zensical is an option if you're ready to switch to a new
    generator. Check its plugin support first, since other plugins are
    ignored.
*   **You're starting new documentation and want the MkDocs plugin
    ecosystem:** MkDocs NG. `mkdocs new` creates a site to start from.
*   **Staying on MkDocs 1.6.1** keeps working for now, but bugs stay unfixed
    and it declares support only for Python 3.8 to 3.12.
*   **The MkDocs 2.0 pre-releases** can't build existing sites. Avoid
    installing them with `pip install --pre` or `uv --prerelease allow`.

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

## Build speed

We built the same generated site with each tool: Markdown pages with
headings, lists, tables, code blocks and links between pages, in sections of
49 pages. Times are for a clean build, one tool after another, on a 4-core
Linux machine with 16 GB of memory, Python 3.13 and Node.js 22, measured on
2026-11-02. Python tools are the median of 3 runs, the others of 1. The
script is [`benchmarks/compare.py`](https://github.com/mkdocs-ng/mkdocs/tree/main/benchmarks),
so you can repeat it on your own machine.

### Clean build of 1,000 pages

Tool | Theme | Time
--- | --- | ---
MkDocs NG 1.11.0rc1 | `mkdocs` | 9.3 s
MkDocs NG 1.11.0rc1 | [Sumi](https://sumi.mkdocs-ng.org/) 0.2.0 | 12.7 s
MkDocs NG 1.11.0rc1 | Material for MkDocs (`mkdocs-ng-material` 9.8.0) | 13.4 s
Zensical 0.0.74 | Its own | 18.2 s; 6.4 s when its cache is kept
ProperDocs 1.6.7 | `mkdocs` | 19.9 s
MkDocs 1.6.1 | `mkdocs` | 20.3 s
Astro Starlight 0.42.8 | Its own | 21.6 s
Sphinx 9.2, 4 processes | Alabaster | 25.8 s
ProperDocs 1.6.7 | Material for MkDocs 9.8.0 | 35.0 s
MkDocs 1.6.1 | Material for MkDocs 9.8.0 | 37.1 s
VitePress 1.6.4 | Its own | 100.9 s
Docusaurus 3.10.2 | Its own | 108.5 s

Each tool ran with its default settings and built-in search. Zensical keeps a
cache of earlier builds in `.cache`; its first time is with that cache
cleared (`zensical build -c`), the second with it kept, after a build with no
changes.

### Clean build of 5,000 pages

Tool | Theme | Time
--- | --- | ---
Zensical 0.0.74, cache kept | Its own | 59.2 s
MkDocs NG 1.11.0rc1 | `mkdocs` | 59.6 s
MkDocs NG 1.11.0rc1 | Sumi 0.2.0 | 67.6 s
MkDocs NG 1.11.0rc1 | Material for MkDocs (`mkdocs-ng-material` 9.8.0) | 134.5 s
Zensical 0.0.74, cache cleared | Its own | 185.5 s
MkDocs 1.6.1 | `mkdocs` | 340.0 s

With Material for MkDocs every page holds the whole navigation, so this site
is more than 4 GB of HTML, which is most of the time it takes. Zensical's
cache for it takes another 8 GB.

### Showing an edit in `serve`

How long after saving a page of the 1,000-page site the development server
serves the changed page, median of 5 edits:

Tool | Theme | Time
--- | --- | ---
Zensical 0.0.74 | Its own | 0.8 s
MkDocs NG 1.11.0rc1 | `mkdocs` | 2.4 s
MkDocs NG 1.11.0rc1 | Sumi 0.2.0 | 3.3 s
MkDocs NG 1.11.0rc1 | Material for MkDocs (`mkdocs-ng-material` 9.8.0) | 6.0 s
MkDocs 1.6.1 | `mkdocs` | 19.6 s
MkDocs 1.6.1 | Material for MkDocs 9.8.0 | 36.1 s

Zensical rebuilds only the pages that changed, while MkDocs NG rebuilds the
whole site, because plugins can change any page when one changes. It
reuses the rendered Markdown of unchanged pages and doesn't rewrite files
whose content stays the same.

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

# Is MkDocs Still Maintained?

The state of MkDocs today, and what it means for your site.

---

Short answer: **upstream MkDocs 1.x is no longer developed.** Its last release
is 1.6.1, from 2024-08-30. Upstream work moved to MkDocs 2.0, a rewrite that
can't build existing sites. Your site keeps building on 1.6.1 for now, and
[MkDocs NG](#what-is-mkdocs-ng) continues 1.x with the same `mkdocs` command,
`mkdocs.yml`, plugins and themes.

Facts on this page were checked on 2026-11-14 against the PyPI release history
and documentation of each project; see [Sources](#sources). If something here
is wrong or out of date, please [open an issue].

## What is the state of MkDocs 1.x?

There has been no release of MkDocs 1.x since 1.6.1 on 2024-08-30.
`pip install mkdocs` still installs it, and sites, plugins and themes built
for it keep working. Bugs reported since then stay unfixed, and 1.6.1 declares
support for Python 3.8 to 3.12 only. Many of the bugs that stayed open
upstream are listed, with their fixes, in
[Fixed Upstream Issues](../about/fixed-upstream-issues.md).

## What is MkDocs 2.0?

MkDocs 2.0 is a rewrite, published as pre-releases of the `mkdocs` package
since 2026-08-28; the latest is 2.0.dev6, from 2026-09-15. It has no
configuration file, plugins or themes: it builds a folder of Markdown files
with one Jinja template, and stops with an error when it finds a
`mkdocs.yml`. Existing sites can't be built with it.

Because these are pre-releases, `pip install mkdocs` doesn't install them.
`pip install --pre mkdocs` and `uv --prerelease allow` do, so avoid those in
the environment you build your site in.

## Will my site stop building?

Not today. With `mkdocs` pinned below 2.0, for example `mkdocs<2`, your site
keeps building as it does now. What it doesn't get on 1.6.1 is fixes: for
bugs, for new Python versions, and for new versions of Python-Markdown, Jinja
and the other libraries it uses. The longer a site stays on 1.6.1, the more
likely one of those breaks it.

## Is Material for MkDocs still maintained?

Material for MkDocs is in maintenance mode, with critical fixes and security
updates until its end of life on 2027-05-05. Its team now develops Zensical.
[Material for MkDocs End of Life](material-end-of-life.md) lists your options,
including MkDocs NG Material, which keeps the `material` theme maintained
after that date.

## What are the alternatives to MkDocs?

For an existing MkDocs site, these are the ways forward:

Project | What it is | Runs MkDocs plugins | Latest release
--- | --- | --- | ---
[MkDocs NG](#what-is-mkdocs-ng) | Maintained fork of MkDocs 1.x, same `mkdocs` command | Yes | 1.11.2 (2026-11-11)
[ProperDocs] | Fork of MkDocs 1.6, with its own `properdocs` command | Yes | 1.6.7 (2026-03-20)
[Zensical] | New generator from the team behind Material for MkDocs | No; reimplements about 30 popular plugins | 0.1.1 (2026-11-10)
MkDocs 1.6.1 | The last upstream 1.x release | Yes | 1.6.1 (2024-08-30)

[MkDocs Alternatives Compared](../about/comparison.md) compares them in detail,
with build times, and says which one suits which site.

## What is MkDocs NG?

MkDocs NG is a maintained fork of MkDocs 1.x, published on PyPI as
`mkdocs-ng`. It keeps the `mkdocs` command, `mkdocs.yml`, `import mkdocs` and
the plugin and theme APIs, so switching is a package change:

```bash
pip install mkdocs-ng
```

*   **Your plugins keep working.** Every change is tested by building sites
    with around 30 popular plugins, themes and Markdown extensions.
*   **Regular releases.** Nine releases since April 2026, the latest on
    2026-11-11; see the [release notes](../about/release-notes.md).
*   **A dated support promise.** MkDocs NG 1.x gets bug, security and
    compatibility fixes until at least 2028-12-31; see
    [Versioning and support](../about/release-notes.md#versioning-and-support).
*   **Current Python.** It supports Python 3.10 to 3.15.
*   **Open governance.** Who maintains it, how decisions are made and what
    happens if a maintainer steps away is written down in
    [Governance](../about/governance.md).

To try it on your site before you change anything, see
[Switching to MkDocs NG](migrating.md#try-it-first). Switching back is the
same one-line change.

## Sources

*   PyPI release history:
    [mkdocs](https://pypi.org/project/mkdocs/#history),
    [mkdocs-ng](https://pypi.org/project/mkdocs-ng/#history),
    [properdocs](https://pypi.org/project/properdocs/#history),
    [zensical](https://pypi.org/project/zensical/#history).
*   MkDocs 2.0: the [package description](https://pypi.org/project/mkdocs/2.0.dev6/)
    and the source code of 2.0.dev6.
*   Material for MkDocs maintenance:
    [upcoming changes](https://zensical.org/upcoming-changes/#material-for-mkdocs).
*   Zensical:
    [MkDocs plugin support](https://zensical.org/docs/compatibility/mkdocs/plugins/).

[open an issue]: https://github.com/mkdocs-ng/mkdocs/issues
[ProperDocs]: https://properdocs.org/
[Zensical]: https://zensical.org/

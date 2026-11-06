# Material for MkDocs End of Life

Your options when Material for MkDocs stops being maintained.

---

Material for MkDocs is in maintenance mode. Its maintainers have announced
that it reaches end of life on 2027-05-05, with critical fixes and security
updates until then, and version 9.8.0 prints a notice saying so on every
build. After that date your site still builds, but bugs and security issues
are no longer fixed.

You don't have to decide today, and you don't have to rewrite your site. This
page lists the ways forward and who each one suits.

Facts on this page were checked on 2026-11-06; see [Sources](#sources).
Projects change quickly, so check their documentation for the current state.
If something here is wrong or out of date, please [open an issue].

## At a glance

&nbsp; | What changes | Plugins | Maintained after 2027-05-05
--- | --- | --- | ---
Stay on Material 9.8 | Nothing | All MkDocs plugins | No
[MkDocs NG Material](#keep-material-with-mkdocs-ng) | Two package names | All MkDocs plugins | Yes: security and compatibility fixes
[Zensical] | The build tool; the `mkdocs.yml` and the look can stay | About 30 popular ones, reimplemented; others are ignored | Yes
[MaterialX] | The theme package, which adds new features | All MkDocs plugins | Yes, by its author
[Sumi] | The theme, on MkDocs NG | All MkDocs plugins | Yes

## Which one fits

*   **You want the site to stay exactly as it is:** MkDocs NG Material. It
    is Material for MkDocs with the same `material` theme name and the same
    configuration, maintained as part of MkDocs NG. You change two lines in
    your requirements and nothing else.
*   **You're ready to move to a new build tool, and Zensical supports every
    plugin you use:** Zensical, from the team behind Material for MkDocs. It
    reads `mkdocs.yml` and keeps the Material look. Check its
    [plugin list][zensical-plugins] first: plugins it doesn't list, and
    `hooks`, don't run, and their settings are ignored.
*   **You want new features in a Material-style theme:** MaterialX continues
    Material for MkDocs with features of its own. It depends on ProperDocs
    and MkDocs 1.6.
*   **You want a lighter theme made for MkDocs NG:** Sumi reads most Material
    settings and content as is. Its [migration guide][sumi-migrate] lists
    what carries over. You can also start with MkDocs NG Material and move to
    Sumi later.

## Keep Material with MkDocs NG

MkDocs NG is a maintained fork of MkDocs 1.x, and MkDocs NG Material
(`mkdocs-ng-material`) is a fork of Material for MkDocs maintained with it.

*   **Same site.** The `material` theme name, `mkdocs.yml`, `overrides/`,
    Markdown and plugins stay as they are.
*   **Maintained after 2027-05-05.** Until that date, upstream security and
    bug fixes are ported as they are released. After it, MkDocs NG Material
    keeps getting security fixes and compatibility fixes for new versions of
    MkDocs NG, Python, Python-Markdown and PyMdown Extensions. It adds no new
    features of its own.
*   **Tested together.** Every change to MkDocs NG is tested by building
    sites with Material for MkDocs and around 30 popular plugins.
*   **Python 3.10 and newer.** Material for MkDocs 9.8 requires Python 3.11.

### Try it first

To see whether your site builds before you change anything, run it once with
[uv]. It installs everything into a throwaway environment:

```bash
uvx --from mkdocs-ng --with mkdocs-ng-material --with-requirements requirements.txt mkdocs build --strict
```

Point `--with-requirements` at the file that lists your plugins.

### Switch

1.  In your requirements, replace `mkdocs` with `mkdocs-ng` and
    `mkdocs-material` with `mkdocs-ng-material`:

    ```text
    mkdocs-ng
    mkdocs-ng-material
    ```

    If you use the `[imaging]` or `[recommended]` extras, keep them:
    `mkdocs-ng-material[imaging]`.

2.  Install them in the environment you build your site in:

    ```bash
    pip install -U mkdocs-ng mkdocs-ng-material
    ```

3.  Build as usual:

    ```bash
    mkdocs build --strict
    ```

    The end-of-life notice from Material for MkDocs no longer appears.

You don't need to uninstall `mkdocs` or `mkdocs-material`. Plugins that
depend on them can keep installing them, and MkDocs NG and MkDocs NG Material
take precedence. See [Switching to MkDocs NG](migrating.md) for CI, Poetry,
uv and Read the Docs.

### Switching back

To go back, put `mkdocs` and `mkdocs-material` back in your requirements and
reinstall:

```bash
pip uninstall mkdocs-ng mkdocs-ng-material
pip install --force-reinstall mkdocs mkdocs-material
```

Your site needs no changes.

## Sources

*   Material for MkDocs: [home page][material] (end-of-life date) and the
    [9.8.0 release notes][material-980].
*   Zensical: [what changed on November 5, 2026][zensical-changes] and
    [MkDocs plugin support][zensical-plugins].
*   MaterialX: [PyPI page][materialx-pypi] (version 10.2.2 and its
    dependencies).
*   MkDocs NG Material: [documentation][ng-material] and
    [PyPI page][ng-material-pypi].
*   [MkDocs NG and its alternatives](../about/comparison.md) compares the
    build tools.

[open an issue]: https://github.com/mkdocs-ng/mkdocs/issues
[Zensical]: https://zensical.org/
[MaterialX]: https://github.com/jaywhj/mkdocs-materialx
[Sumi]: https://sumi.mkdocs-ng.org/
[sumi-migrate]: https://sumi.mkdocs-ng.org/docs/start/migrate/
[uv]: https://docs.astral.sh/uv/
[material]: https://squidfunk.github.io/mkdocs-material/
[material-980]: https://github.com/squidfunk/mkdocs-material/releases/tag/9.8.0
[zensical-changes]: https://zensical.org/upcoming-changes/
[zensical-plugins]: https://zensical.org/docs/compatibility/mkdocs/plugins/
[materialx-pypi]: https://pypi.org/project/mkdocs-materialx/
[ng-material]: https://material.mkdocs-ng.org/
[ng-material-pypi]: https://pypi.org/project/mkdocs-ng-material/

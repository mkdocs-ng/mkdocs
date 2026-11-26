# Switching to MkDocs NG

Move an existing MkDocs site to MkDocs NG.

---

MkDocs NG is a maintained fork of [MkDocs 1.x][upstream]. It keeps the
`mkdocs` command, `mkdocs.yml`, the plugin and theme APIs and `import mkdocs`,
so switching is a package change, not a migration of your site. Your Markdown,
configuration, plugins and themes stay as they are, and
[switching back](#switching-back) is the same one-line change.

## Try it first

To see whether your site builds with MkDocs NG before you change anything, run
it once with [uv]. `uvx` installs MkDocs NG and your requirements into a
throwaway environment and leaves your own environment and files alone:

```bash
uvx --from mkdocs-ng --with-requirements requirements.txt mkdocs build --strict
```

Point `--with-requirements` at the file that lists your plugins and themes,
or name them with `--with`, for example
`uvx --from mkdocs-ng --with mkdocs-material mkdocs build --strict`. Without
them, the build fails on the first plugin or theme it can't find.

## Switch

1.  Install MkDocs NG into the environment you build your site in. You don't
    need to uninstall `mkdocs` first:

    ```bash
    pip install -U mkdocs-ng
    ```

    With uv: `uv pip install -U mkdocs-ng`, or `uv add mkdocs-ng` in a uv
    project.

2.  Check that the `mkdocs` command now runs MkDocs NG. The path ends in
    `mkdocs_ng/mkdocs`:

    ```console
    $ mkdocs --version
    mkdocs, version 1.11.0 from /path/to/site-packages/mkdocs_ng/mkdocs (Python 3.12)
    ```

3.  Build your site as usual, ideally with `--strict` so that anything that
    changed shows up as an error:

    ```bash
    mkdocs build --strict
    ```

4.  Replace `mkdocs` with `mkdocs-ng` wherever your dependencies are listed,
    so CI and other machines install it too. See
    [Updating your dependencies](#updating-your-dependencies).

That's it. Commands such as `mkdocs serve` and `mkdocs gh-deploy` work as
before.

> NOTE:
> MkDocs NG 1.11 and newer install alongside upstream MkDocs. With MkDocs NG
> 1.9 and earlier, run `pip uninstall mkdocs` before installing it, and again
> after installing a plugin or theme. Upgrading to 1.11 fixes that, even in
> an environment where upstream MkDocs had already overwritten MkDocs NG.

## Updating your dependencies

Plugins and themes, including Material for MkDocs, depend on the `mkdocs`
package, so upstream MkDocs keeps getting installed next to MkDocs NG. That's
expected: MkDocs NG always takes precedence, whatever the install order. Leave
the upstream package installed, and list `mkdocs-ng` instead of `mkdocs`:

In `requirements.txt`:

```text
mkdocs-ng
mkdocs-material
```

In `pyproject.toml`, in `[project]` or in a dependency group:

```toml
[project]
dependencies = ["mkdocs-ng", "mkdocs-material"]

[dependency-groups]
docs = ["mkdocs-ng", "mkdocs-material"]
```

With pipx, replace the app and inject your plugins and themes:

```bash
pipx uninstall mkdocs
pipx install mkdocs-ng
pipx inject mkdocs-ng mkdocs-material
```

With Poetry, swap the package in the group that lists it:

```bash
poetry remove --group docs mkdocs
poetry add --group docs mkdocs-ng
```

On Read the Docs, nothing changes in `.readthedocs.yaml`. Its
`python.install` step installs the requirements file you updated above.

In a GitHub Actions workflow, or any CI script, change the package name in the
install step:

```yaml
- run: pip install mkdocs-ng mkdocs-material
```

To pin a version, pin `mkdocs-ng`, for example `mkdocs-ng>=1.11,<2`.

In a uv project you can keep upstream MkDocs from being installed at all. See
[Keeping upstream MkDocs out](installation.md#keeping-upstream-mkdocs-out).

## What changes

Nothing in your configuration needs to change. A few fixes since upstream
MkDocs 1.6.1 change behavior in ways you might notice:

*   **Python 3.10 or newer is required.** Upstream MkDocs 1.6.1 supports
    Python 3.8 and 3.9 as well.
*   **`mkdocs build --quiet --strict` fails when there are warnings.** Upstream,
    `--quiet` stopped warnings from being counted, so such builds passed with
    broken links. Run without `--quiet` to see the warnings.
*   **Deprecated options no longer fail `strict` builds.** Their notices are
    logged at INFO level instead of WARNING. Removed options are still errors.
*   **Built-in search indexes English stop words** such as `while`, `if` and
    `for`, so searching for them finds results. Set the search plugin's
    `stop_words: true` for the old behavior.
*   **The built-in themes load nothing from CDNs** and no longer include the
    Universal Analytics (`analytics.js`) snippet, as Google shut that service
    down in 2023. The deprecated `google_analytics` option has no effect; use the
    theme's `analytics.gtag` option instead.
*   **Plugins don't print the "switch to ProperDocs" warning.** Plugins such
    as `mkdocs-redirects` and `mkdocs-gen-files` print it when run by the
    `mkdocs` command. MkDocs NG sets `DISABLE_MKDOCS_2_WARNING=true` unless
    you have set it yourself.

The [release notes] list every change, and [Fixed Upstream Issues] lists the
upstream bugs that are fixed.

## Plugins and themes

Plugins and themes written for MkDocs 1.x work unchanged: MkDocs NG provides
the same plugin events, configuration classes and theme templates. Every
change to MkDocs NG is tested by building sites with these popular plugins,
themes and Markdown extensions, installed the way users install them, and the
test runs again every week to catch new plugin releases:

[markdown-exec](https://pypi.org/project/markdown-exec/), [mike](https://pypi.org/project/mike/), [mkdocs-autorefs](https://pypi.org/project/mkdocs-autorefs/), [mkdocs-awesome-nav](https://pypi.org/project/mkdocs-awesome-nav/), [mkdocs-awesome-pages-plugin](https://pypi.org/project/mkdocs-awesome-pages-plugin/), [mkdocs-bibtex](https://pypi.org/project/mkdocs-bibtex/), [mkdocs-cinder](https://pypi.org/project/mkdocs-cinder/), [mkdocs-click](https://pypi.org/project/mkdocs-click/), [mkdocs-encryptcontent-plugin](https://pypi.org/project/mkdocs-encryptcontent-plugin/), [mkdocs-gen-files](https://pypi.org/project/mkdocs-gen-files/), [mkdocs-git-authors-plugin](https://pypi.org/project/mkdocs-git-authors-plugin/), [mkdocs-git-revision-date-localized-plugin](https://pypi.org/project/mkdocs-git-revision-date-localized-plugin/), [mkdocs-glightbox](https://pypi.org/project/mkdocs-glightbox/), [mkdocs-include-markdown-plugin](https://pypi.org/project/mkdocs-include-markdown-plugin/), [mkdocs-jupyter](https://pypi.org/project/mkdocs-jupyter/), [mkdocs-kroki-plugin](https://pypi.org/project/mkdocs-kroki-plugin/), [mkdocs-literate-nav](https://pypi.org/project/mkdocs-literate-nav/), [mkdocs-macros-plugin](https://pypi.org/project/mkdocs-macros-plugin/), [mkdocs-markdownextradata-plugin](https://pypi.org/project/mkdocs-markdownextradata-plugin/), [mkdocs-material](https://pypi.org/project/mkdocs-material/), [mkdocs-mermaid2-plugin](https://pypi.org/project/mkdocs-mermaid2-plugin/), [mkdocs-minify-plugin](https://pypi.org/project/mkdocs-minify-plugin/), [mkdocs-monorepo-plugin](https://pypi.org/project/mkdocs-monorepo-plugin/), [mkdocs-redirects](https://pypi.org/project/mkdocs-redirects/), [mkdocs-rss-plugin](https://pypi.org/project/mkdocs-rss-plugin/), [mkdocs-static-i18n](https://pypi.org/project/mkdocs-static-i18n/), [mkdocs-swagger-ui-tag](https://pypi.org/project/mkdocs-swagger-ui-tag/), [mkdocs-techdocs-core](https://pypi.org/project/mkdocs-techdocs-core/), [mkdocstrings-python](https://pypi.org/project/mkdocstrings/), [neoteroi-mkdocs](https://pypi.org/project/neoteroi-mkdocs/), [plantuml-markdown](https://pypi.org/project/plantuml-markdown/), [pymdown-extensions](https://pypi.org/project/pymdown-extensions/).

The [plugin catalog] marks every project in this test. If a plugin or theme
that works with upstream MkDocs fails with MkDocs NG, please [open an issue].

### Material for MkDocs

Material for MkDocs works with MkDocs NG and is part of the tests above. Its
maintainers have announced that it reaches end of life on 2027-05-05, and it
prints a notice saying so on every build.

To keep your site exactly as it is after that date, replace
`mkdocs-material` with `mkdocs-ng-material` in your requirements.
[MkDocs NG Material][ng-material] is Material for MkDocs maintained as part of
MkDocs NG, with the same `material` theme name and configuration, and it keeps
getting security and compatibility fixes after 2027-05-05. When you want to
move on, [Sumi] is the theme made for MkDocs NG. It reads most Material
configuration and content as-is, and its [migration guide][sumi-migrate] lists
what carries over. See [Material for MkDocs End of Life] for all the options.

## Coming from ProperDocs

[ProperDocs] is another fork of MkDocs 1.6 with its own `properdocs` command,
which reads `properdocs.yml` and falls back to `mkdocs.yml`. To switch, install
MkDocs NG, rename `properdocs.yml` to `mkdocs.yml` if you have one, and run
`mkdocs` instead of `properdocs`. Plugins that moved to ProperDocs, such as
`mkdocs-redirects` and `mkdocs-gen-files`, keep working with MkDocs NG and are
part of its compatibility tests.

## Coming from MkDocs 2.0 pre-releases

The upstream MkDocs 2.0 pre-releases (`pip install --pre mkdocs`) are a
rewrite. As of 2.0.dev6 they don't read `mkdocs.yml`, refuse to run when one
exists, and don't support plugins or themes. If one got installed, for example
by `pip install --pre` or `uv --prerelease allow`, install MkDocs NG 1.11 or
newer and the `mkdocs` command runs MkDocs NG again. To remove the
pre-release, pin `mkdocs<2` next to `mkdocs-ng`.

## Switching back

To go back to upstream MkDocs, uninstall MkDocs NG and reinstall upstream
MkDocs, which restores its `mkdocs` command:

```bash
pip uninstall mkdocs-ng
pip install --force-reinstall --no-deps mkdocs
```

Your site needs no changes, unless you started using features that upstream
MkDocs doesn't have, such as the [`llms_txt`](configuration.md#llmstxt)
plugin or a list of files in [`INHERIT`](configuration.md#configuration-inheritance).

[upstream]: https://github.com/mkdocs/mkdocs
[release notes]: ../about/release-notes.md
[Fixed Upstream Issues]: ../about/fixed-upstream-issues.md
[open an issue]: https://github.com/mkdocs-ng/mkdocs/issues
[ProperDocs]: https://properdocs.org/
[uv]: https://docs.astral.sh/uv/
[plugin catalog]: https://github.com/mkdocs-ng/catalog
[Sumi]: https://sumi.mkdocs-ng.org/
[sumi-migrate]: https://sumi.mkdocs-ng.org/docs/start/migrate/
[ng-material]: https://material.mkdocs-ng.org/
[Material for MkDocs End of Life]: material-end-of-life.md

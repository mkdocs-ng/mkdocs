# Upstream Issues Fixed in MkDocs NG

MkDocs NG is a maintained fork of [mkdocs/mkdocs], which is no longer under
active development. Beyond keeping up with new Python releases and
dependencies, the fork resolves long-standing issues that were reported
upstream but never fixed there.

This page tracks notable upstream issues that are already resolved in MkDocs
NG. If you are affected by one of them, upgrading is a one-line change — the
package name on PyPI is `mkdocs-ng`, while the `mkdocs` command and all
configuration stay the same:

```bash
pip uninstall mkdocs && pip install -U mkdocs-ng
```

## Development server

Upstream issue | Symptom | Fixed in
-------------- | ------- | --------
[#4032], [#4014], [#4055], [#4081] | With `click>=8.2`, `mkdocs serve` stopped watching for file changes, live reload only worked when `--livereload` was passed explicitly (often misdiagnosed as a WSL problem), and `use_directory_urls` was overridden. | 1.7.0 (#4), 1.7.3 (#60)
[#2519] | Editor temporary files (vim swap files, `~` backups, Emacs auto-save) triggered pointless rebuilds. | 1.7.3 (#55)
[#4001] | Edge-case markup such as `<<>>` crashed the build with `AssertionError` from Python's `html.parser` (seen on Python 3.13.5+). | 1.7.3 (#51)

## Built-in themes

Upstream issue | Symptom | Fixed in
-------------- | ------- | --------
[#2171] | Built-in themes loaded resources from CDNs, sharing visitor data with third parties and breaking offline use. highlight.js is now bundled locally and the themes contain no CDN references. | 1.7.4 (#75)
[#3630] | The long-dead Universal Analytics (`analytics.js`) snippet was hardcoded into the themes. It is removed; use `analytics.gtag` (GA4) or override the `analytics` template block. | 1.7.4 (#84)
[#4045] | Disabling `highlightjs` broke switching between light and dark mode in the mkdocs theme. | 1.7.1 (#39)

## Search

Upstream issue | Symptom | Fixed in
-------------- | ------- | --------
[#4167] | Searching for words that happen to be English stop words — `while`, `if`, `for`, `from` and many more — returned no results, even though they are meaningful keywords in technical documentation. Stop words are now indexed by default; a `stop_words` plugin option restores the old behavior. | 1.7.4 (#80)

## Validation

Upstream issue | Symptom | Fixed in
-------------- | ------- | --------
[#3690] | Anchor validation reported false positives for anchors generated late by Markdown extensions, e.g. `pymdownx.tabbed` with `combine_header_slug`. | 1.7.1 (#34)
[#3703] | The "does not contain an anchor" warning gave no hint when the only problem was letter case; it now suggests the correct anchor (`did you mean '#conflicts'?`). | 1.7.4 (#83)

## Python API

Upstream issue | Symptom | Fixed in
-------------- | ------- | --------
[#1240] | No stable programmatic API — running MkDocs from Python code required subprocess calls or private imports. MkDocs NG provides `mkdocs.build()` and `mkdocs.serve()`. | 1.7.4 (#76)

## Also worth knowing

*   Python 3.13 and 3.14 are fully supported and tested (added in 1.7.0), while
  upstream's last release predates them.
*   Version numbers marked 1.7.4 refer to the upcoming release; the fixes are
  already merged on the `main` branch.
*   Found another upstream issue you'd like to see fixed here? Please
  [open an issue].

[mkdocs/mkdocs]: https://github.com/mkdocs/mkdocs
[#1240]: https://github.com/mkdocs/mkdocs/issues/1240
[#2171]: https://github.com/mkdocs/mkdocs/issues/2171
[#2519]: https://github.com/mkdocs/mkdocs/issues/2519
[#3630]: https://github.com/mkdocs/mkdocs/issues/3630
[#3690]: https://github.com/mkdocs/mkdocs/issues/3690
[#3703]: https://github.com/mkdocs/mkdocs/issues/3703
[#4001]: https://github.com/mkdocs/mkdocs/issues/4001
[#4014]: https://github.com/mkdocs/mkdocs/issues/4014
[#4032]: https://github.com/mkdocs/mkdocs/issues/4032
[#4045]: https://github.com/mkdocs/mkdocs/issues/4045
[#4055]: https://github.com/mkdocs/mkdocs/issues/4055
[#4081]: https://github.com/mkdocs/mkdocs/issues/4081
[#4167]: https://github.com/mkdocs/mkdocs/issues/4167
[open an issue]: https://github.com/mkdocs-ng/mkdocs/issues

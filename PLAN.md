# MkDocs-NG Feature Plan

Curated from [mkdocs/mkdocs issues](https://github.com/mkdocs/mkdocs/issues) and
[discussions](https://github.com/mkdocs/mkdocs/discussions), sorted by user demand
(reactions :+1: + comments).  Items already addressed by mkdocs-ng are excluded.

---

## 🔥 P0 – High Demand / Urgent Bugs

### 1. Remove CDNs from built-in themes
- **Issue**: [mkdocs/mkdocs#2171](https://github.com/mkdocs/mkdocs/issues/2171)
- **👍**: 18  ·  💬: 7
- **Description**: The built-in `mkdocs` and `readthedocs` themes load fonts (e.g. Lato, Roboto Slab) and CSS from Google Fonts / CDNs.  Users who self-host documentation want full offline / privacy-respecting operation without third-party requests.  Some fonts are already bundled, but `base.html` still references external URLs.
- **Labels**: `Theme-mkdocs`, `Theme-readthedocs`

### 2. Improve `mkdocs serve` performance & authoring experience
- **Issue**: [mkdocs/mkdocs#3695](https://github.com/mkdocs/mkdocs/issues/3695)
- **👍**: 15  ·  💬: 22
- **Description**: Opened by the maintainer of Material for MkDocs.  Proposes collaborative improvements to `mkdocs serve`: faster rebuilds, smarter watcher, better error messages, and lowering the friction of the write-build-check loop.  Concrete ideas include incremental builds, file-system-level caching, and a plugin-friendly architecture for serve hooks.

### 3. Stable public Python API
- **Issue**: [mkdocs/mkdocs#1240](https://github.com/mkdocs/mkdocs/issues/1240)
- **👍**: 10  ·  💬: 8
- **Description**: There is no officially supported way to invoke MkDocs from Python code.  Users currently call internal functions (e.g. `build_command()`, `serve_command()`) or shell out via `subprocess`.  A documented, stable API (e.g. `mkdocs.build()`, `mkdocs.serve()`) is needed for build-system integrations, CI scripts, and programmatic usage.
- **Labels**: `Enhancement`, `Needs design decision`

### 4. Remove hardcoded Google Analytics from theme
- **Issue**: [mkdocs/mkdocs#3630](https://github.com/mkdocs/mkdocs/issues/3630)
- **👍**: 8  ·  💬: 1
- **Description**: The `mkdocs` theme hardcodes a Google Analytics snippet via the `analytics` template tag block.  This is out of place in a privacy-conscious static site generator.  Proposal: drop the built-in GA support entirely and document how to add analytics via `extrahead` template overrides instead.
- **Labels**: `Cleanup`

### 5. Support multiple `INHERIT` configs
- **Issue**: [mkdocs/mkdocs#2624](https://github.com/mkdocs/mkdocs/issues/2624)
- **👍**: 8  ·  💬: 3
- **Description**: `INHERIT` currently accepts only a single file path.  Users with complex setups want to compose configuration from multiple files (e.g. one for markdown extensions, one for plugins, one for extra settings).  Proposal: allow `INHERIT` to accept a list of paths.
- **Labels**: `Configuration`

### 6. Fix `mkdocs serve --livereload` not triggering automatically
- **Issue**: [mkdocs/mkdocs#4055](https://github.com/mkdocs/mkdocs/issues/4055)
- **👍**: 25  ·  💬: 6
- **Description**: In recent versions, livereload no longer works unless `--livereload` is passed explicitly.  mkdocs-ng **partially** addresses this through PRs restoring `--livereload`, but some users still report it not working by default.  This may intersect with the Click version issue (#4032) and WSL-specific problems (#4081).
- **Status in mkdocs-ng**: ✅ `--livereload` flag restored; default behaviour should be verified

### 7. `mkdocs serve` does not watch files (Click ≥ 8.3.0 regression)
- **Issue**: [mkdocs/mkdocs#4032](https://github.com/mkdocs/mkdocs/issues/4032)
- **👍**: 66  ·  💬: 31
- **Description**: Starting with Click 8.3.0, file watching breaks entirely — changes no longer trigger a rebuild.  Workaround is pinning `click<=8.2.1`.  This is the highest-reaction open issue by far.
- **Status in mkdocs-ng**: needs verification — `pyproject.toml` currently allows `click >=7.0`; CI pins to `8.1.8` for min-version tests, but the runtime constraint does not prevent 8.3.0.

---

## ⚡ P1 – Important Features & Fixes

### 8. Live reload triggers on editor temp / hidden files
- **Issue**: [mkdocs/mkdocs#2519](https://github.com/mkdocs/mkdocs/issues/2519)
- **👍**: 7  ·  💬: 18
- **Description**: Editors like Vim create swap files (`.foo.md.swp`) and hidden files that cause `mkdocs serve` to constantly rebuild even though those files aren't included in the output.  The watcher should ignore dot-files and editor temp files by default, with an opt-in mechanism for directories like `.well-known/`.
- **Labels**: `Command - serve`, `Configuration`

### 9. Add `rel="external"` to outbound links
- **Issue**: [mkdocs/mkdocs#3914](https://github.com/mkdocs/mkdocs/issues/3914)
- **👍**: 7  ·  💬: 0
- **Description**: External (absolute URL) links should be automatically annotated with `rel="external"` so theme authors and users can style them differently (e.g. add an external-link icon).  This became more important after Material for MkDocs switched to always using absolute URLs for navigation.
- **Labels**: `Enhancement`

### 10. Cache busting for static assets
- **Issue**: [mkdocs/mkdocs#1979](https://github.com/mkdocs/mkdocs/issues/1979)
- **👍**: 5  ·  💬: 34
- **Description**: MkDocs has no built-in mechanism to append content hashes to CSS/JS filenames for cache busting.  After a documentation site update, returning visitors may get stale cached assets.  Implementation could be via a plugin (preferred by maintainers) or core feature.
- **Labels**: `Enhancement`, `Plugins`

### 11. Decouple built-in search from core
- **Issue**: [mkdocs/mkdocs#3698](https://github.com/mkdocs/mkdocs/issues/3698)
- **👍**: 5  ·  💬: 8
- **Description**: The search plugin (based on lunr.js) is bundled with core MkDocs.  lunr.js is unmaintained (last commit ~4 years ago) with known bugs.  Proposal: extract search into a standalone installable package, decouple it from the core release cycle, and pave the way for a modern replacement.
- **Labels**: `Search`

### 12. Decouple built-in themes from core
- **Issue**: [mkdocs/mkdocs#3636](https://github.com/mkdocs/mkdocs/issues/3636)
- **👍**: 4  ·  💬: 17
- **Description**: The core maintainers agreed to move the `readthedocs` theme (and possibly `mkdocs` theme) into separate repos and installable packages.  This simplifies core, allows themes to be versioned independently, and opens the door for new default themes.
- **Labels**: `Cleanup`

### 13. Support root directory as `docs_dir`
- **Issue**: [mkdocs/mkdocs#3450](https://github.com/mkdocs/mkdocs/issues/3450) / [PR #3519](https://github.com/mkdocs/mkdocs/pull/3519)
- **👍**: 3  ·  💬: 15
- **Description**: MkDocs currently forbids placing `mkdocs.yml` inside the `docs_dir`.  Users who want to use the project root as `docs_dir` (e.g. monorepos, projects with `README.md` as homepage) need to work around this restriction.  The PR #3519 removes the validation check and auto-excludes config/site files from the docs.
- **Labels**: `Navigation`

---

## 📋 P2 – Nice to Have

### 14. Support text fragment links (ignore them during validation)
- **Issue**: [mkdocs/mkdocs#3952](https://github.com/mkdocs/mkdocs/issues/3952)
- **👍**: 3  ·  💬: 0
- **Description**: [Text fragment links](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment/Text_fragments) (`#:~:text=…`) are a modern web standard for linking to specific text on a page.  MkDocs' anchor validator incorrectly reports them as broken anchors.  The validator should recognize and skip `#:~:text=` fragments.
- **Labels**: `Validation`

### 15. Auto-switch port when the default port is busy
- **Issue**: [mkdocs/mkdocs#3496](https://github.com/mkdocs/mkdocs/issues/3496)
- **👍**: 3  ·  💬: 0
- **Description**: If port 8000 is already in use, `mkdocs serve` should automatically try the next available port (8001, 8002, …) instead of failing.  A related PR (#3498) adds a manual port override flag, but automatic fallback is the desired UX.
- **Labels**: `Command - serve`

### 16. Smart section titles when no nav is configured
- **Issue**: [mkdocs/mkdocs#3356](https://github.com/mkdocs/mkdocs/issues/3356)
- **👍**: 3  ·  💬: 6
- **Description**: When no `nav` is defined in `mkdocs.yml`, section titles for sub-directories should be derived from the index page's title metadata or first heading, rather than displaying raw directory names.  This is already a feature in Material for MkDocs (`navigation.smart-section-titles`), but should be available in core.
- **Labels**: `Navigation`, `Titles`

### 17. Support GitHub-style Markdown Alerts
- **Issue**: [mkdocs/mkdocs#3997](https://github.com/mkdocs/mkdocs/issues/3997)
- **👍**: 2  ·  💬: 2
- **Description**: GitHub-flavored markdown alert blocks (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`) should render as styled callouts in MkDocs.  This would improve portability of docs authored on GitHub to MkDocs sites.

### 18. Extend `on_page_context` with Jinja2 Environment reference
- **Issue**: [mkdocs/mkdocs#3709](https://github.com/mkdocs/mkdocs/issues/3709)
- **👍**: 2  ·  💬: 1
- **Description**: The `on_page_context` plugin event should expose the Jinja2 `Environment` object so plugins can apply per-page template filters and globals.  This is needed for multi-instance plugins (e.g. Material for MkDocs blog plugin) where each plugin instance needs to register its own template functions per page.

### 19. Deprecated options should emit `INFO`, not `WARNING`
- **Issue**: [mkdocs/mkdocs#3696](https://github.com/mkdocs/mkdocs/issues/3696)
- **👍**: 2  ·  💬: 5
- **Description**: The `Deprecated` config helper emits `WARNING` messages, which break `--strict` mode.  Since deprecated options are still functional (just discouraged), they should emit `INFO`-level messages so strict builds don't fail on deprecation notices alone.

### 20. Custom import paths for `markdown_extensions`
- **Issue**: [mkdocs/mkdocs#3772](https://github.com/mkdocs/mkdocs/issues/3772)
- **👍**: 1  ·  💬: 29
- **Description**: Users who write small project-specific Markdown extensions need a way to add the extension's directory to `sys.path` from within `mkdocs.yml`, without requiring `PYTHONPATH` hacks or pip-installable packages.  A config option like `markdown_extensions_path: ["extensions/"]` would suffice.

### 21. Respect display text when the same `.md` file appears in nav multiple times
- **Issue**: [mkdocs/mkdocs#3710](https://github.com/mkdocs/mkdocs/issues/3710)
- **👍**: 2  ·  💬: 3
- **Description**: When a file is referenced multiple times in `nav` with different display names (e.g. `- 'French Main Dishes': 'French Cuisine.md'` and `- 'French Desserts': 'French Cuisine.md'`), MkDocs now overrides both entries with the first title encountered.  Previously, each entry kept its set display text.

---

## 🔧 P3 – Maintenance & Infrastructure

### 22. New default theme
- **Issue**: [mkdocs/mkdocs#3680](https://github.com/mkdocs/mkdocs/issues/3680)
- **👍**: 0  ·  💬: 6
- **Description**: The default `mkdocs` theme is dated (Bootstrap 3).  A new, modern, optionally installable default theme should be designed and shipped separately, as part of the theme decoupling effort (#3636).

### 23. Title source precedence controls
- **Issue**: [mkdocs/mkdocs#3532](https://github.com/mkdocs/mkdocs/issues/3532)
- **👍**: 0  ·  💬: 37
- **Description**: When a page has both a YAML `title` meta field and an H1 heading, the precedence between them (and the `nav` display name) can be surprising.  Users want more control over which source wins, ideally configurable per page or globally.

### 24. Fix `use_directory_urls: true` with Click ≥ 8.2.2
- **Issue**: [mkdocs/mkdocs#4014](https://github.com/mkdocs/mkdocs/issues/4014)
- **👍**: 7  ·  💬: 5
- **Description**: Click 8.2.2 changed path behavior that broke `use_directory_urls: true` — generated links become `page/index.html` instead of `page/`.  This is related to #4032 and may require pinning or fixing the Click integration.
- **Status in mkdocs-ng**: unknown — needs testing with Click ≥ 8.2.2

### 25. WSL: `mkdocs serve` fails to live reload
- **Issue**: [mkdocs/mkdocs#4081](https://github.com/mkdocs/mkdocs/issues/4081)
- **👍**: 2  ·  💬: 2
- **Description**: On WSL with ext4 filesystem, file-watching doesn't trigger livereload.  May be related to the Click watcher regression (#4032) or filesystem notification limitations in WSL.

---

*Last updated: 2026-04-29*
*Sources: [mkdocs/mkdocs open issues](https://github.com/mkdocs/mkdocs/issues), sorted by reactions*

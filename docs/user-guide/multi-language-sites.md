# Multi-language Sites

Publish your documentation in several languages from one `mkdocs.yml`.

---

> NEW: **New in MkDocs NG 1.11.**

List the languages under [`languages`](configuration.md#languages). The first
one is the default language: it is built at the root of the site, and every
other language is built into a sub-directory named after its code.

```yaml
site_name: My Project
site_url: https://example.com/

languages:
  en: English
  zh:
    name: 简体中文
    site_name: 我的项目
    nav:
      - 首页: index.md
      - 指南: guide.md
```

`mkdocs build` builds the English site into `site/` and the Chinese one into
`site/zh/`. `mkdocs serve` serves both, and reloads both when a file changes.

## Translating pages

Put the translation of a page next to it, with the language code before the
file extension:

```text
docs/
    index.md          # English
    index.zh.md       # Chinese
    guide.md
    guide.zh.md
    img/
        screenshot.png
```

Links between pages and to images use the names without the language code,
such as `[the guide](guide.md)`, in every language. The same goes for `nav`.
Any file can have a translation, so `img/screenshot.zh.png` replaces
`img/screenshot.png` on the Chinese site.

If you would rather keep each language in a directory of its own, give that
language a [`docs_dir`](configuration.md#docs_dir), with the same file names
as the default language's:

```yaml
languages:
  en: English
  zh:
    name: 简体中文
    docs_dir: docs-zh
    edit_uri: edit/main/docs-zh/
```

### Pages that aren't translated yet

A page that has no translation is built from the default language's version,
so every language has every page and no link is broken. Themes can tell that a
page is shown untranslated (see [For theme authors](#for-theme-authors)) and
say so to readers; Sumi shows a note at the top of the page.

To leave untranslated pages out of a language instead, set `fallback: false`:

```yaml
languages:
  en: English
  zh:
    name: 简体中文
    fallback: false
```

Images and other files are always taken from the default language when a
language has no version of its own.

## Settings for one language

Apart from `name`, `path` and `fallback`, every key of a language overrides
that setting of `mkdocs.yml` for that language. Mappings are merged, the same
way as with [`INHERIT`](configuration.md#configuration-inheritance), and other
values are replaced. Typical ones are `site_name`, `site_description`, `nav`,
`copyright`, `edit_uri` and parts of `theme` or `extra`:

```yaml
languages:
  en: English
  de:
    name: Deutsch
    site_name: Mein Projekt
    copyright: Alle Rechte vorbehalten
    theme:
      logo: img/logo-de.svg
    extra:
      announcement: Neu in Version 2!
```

These are set for you:

*   **`theme.locale`** is the language code, unless the language sets
    `theme.locale` itself. The default language keeps a `theme.locale` that
    `mkdocs.yml` sets.
*   **`site_url`** gets the language's path added, such as
    `https://example.com/zh/`.
*   **`site_dir`** gets the language's path added, such as `site/zh`. It
    can't be set per language.

The keys that describe the language itself:

`name`
:   The name shown in the language switcher. Defaults to the code. The short
    form `zh: 简体中文` sets only the name.

`path`
:   Where the language is built, relative to the site root. Defaults to the
    language code. For example, `zh-Hans: {name: 简体中文, path: zh}` is built
    into `/zh/`. The default language is always at the root.

`fallback`
:   Whether pages that have no translation are built from the default
    language's version. Default: `true`.

## Building one language

Building every language takes longer than building one. While you work on one
language, build or serve only that one with `--language` (or `-L`):

```bash
mkdocs serve --language zh
mkdocs build -L en -L zh
```

## The language switcher

Each page links to the same page in the other languages, and to the home page
of a language that doesn't have it. Themes that read
[`extra.alternate`](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/#site-language-selector),
such as Sumi and Material for MkDocs, show this switcher with no further
setup: MkDocs NG fills in `extra.alternate` for every page, unless you set it
yourself.

## How it works

Each language is built as an ordinary MkDocs site, one after the other, each
with its own configuration and its own instances of the plugins (plugins with
[`on_startup`](../dev-guide/plugins.md#on_startup) are created once and run for
every language, as they do for every rebuild of `mkdocs serve`). A plugin sees
a normal single-language site, so plugins don't need to know about languages.
The search index, the sitemap, `llms.txt` and the files of plugins are made
for each language in its own directory.

## For theme authors

On a multi-language site, templates get an `i18n` variable. It is `None` on
other sites.

```python
{
    "language": {"code": "zh", "name": "简体中文", "path": "zh", "default": False},
    "default_language": "en",
    # True if this page is the default language's version, shown because the
    # current language has no translation of it.
    "fallback": False,
    "languages": [
        {
            "code": "en",
            "name": "English",
            "lang": "en",
            # The same page in this language, relative to the site root of the
            # current language: use it with the `url` filter.
            "link": "../guide/",
            # The full URL, if `site_url` is set (for `hreflang` links).
            "url": "https://example.com/guide/",
            "current": False,
            # False if this language doesn't have the page; `link` then points
            # to the language's home page.
            "available": True,
        },
        ...
    ],
}
```

For example, a language menu and `hreflang` links:

```django
{% if i18n %}
  {% for alt in i18n.languages %}
    <a href="{{ alt.link | url }}" hreflang="{{ alt.lang }}"
       {% if alt.current %}aria-current="true"{% endif %}>{{ alt.name }}</a>
  {% endfor %}
{% endif %}
```

```django
{% if i18n and page %}
  {% for alt in i18n.languages if alt.available %}
    <link rel="alternate" hreflang="{{ alt.lang }}" href="{{ alt.url or (alt.link | url) }}">
  {% endfor %}
{% endif %}
```

Plugins can find the languages in `config.languages`, a list of
`mkdocs.languages.Language` objects, and the language being built with
`mkdocs.languages.current(config)`. Both are `None` on a single-language site.

## Coming from mkdocs-static-i18n

The [mkdocs-static-i18n](https://github.com/ultrabug/mkdocs-static-i18n)
plugin and `languages` both read `page.zh.md` files and `docs/<language>/`
directories. To switch:

1.  Remove the `i18n` plugin from `plugins`.
2.  Move its `languages` list to the top-level `languages` setting. The
    language marked `default: true` goes first. `locale` becomes the key,
    `name` stays, and `site_name`, `nav`, `theme` and the other overrides go
    in the language's entry as they are. `nav_translations` becomes a `nav`
    for that language.
3.  With `docs_structure: folder`, give each language its `docs_dir`, such as
    `docs_dir: docs/zh`, and the default language `docs_dir: docs/en`.

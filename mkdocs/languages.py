"""
Multi-language sites, declared in one `mkdocs.yml`.

```yaml
languages:
  en: English
  zh:
    name: 简体中文
    site_name: 我的项目
```

The first language is the default one and is built at the root of the site.
Every other language is built into a sub-directory named after it (`/zh/`).
The keys of a language other than `name`, `path` and `fallback` override the
config for that language, merged the same way as `INHERIT`.

Each language is built as a separate, ordinary MkDocs build, with its own
config and its own plugin instances. Plugins and themes see a normal
single-language site, so they need nothing special to support this. Themes
that want a language switcher read the `i18n` template variable, or the
`extra.alternate` list that is filled in when the config doesn't set one.

Pages are found in two ways, which can be mixed:

* Suffix: `docs/guide.zh.md` is the Chinese version of `docs/guide.md`.
* Folder: a language that sets its own `docs_dir` takes its pages from there.

A page that has no translation is built from the default language's version
(set `fallback: false` on a language to leave it out instead).
"""

from __future__ import annotations

import dataclasses
import io
import os
import posixpath
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from mkdocs import exceptions, utils
from mkdocs.utils.yaml import _deep_merge

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File
    from mkdocs.structure.pages import Page


_CODE_RE = re.compile(r"^[A-Za-z]{2,3}([-_][A-Za-z0-9]{2,8})*$")
_PATH_RE = re.compile(r"^[A-Za-z0-9._~-]+(/[A-Za-z0-9._~-]+)*$")

# Keys of a language entry that describe the language itself. All others are
# config overrides.
_OWN_KEYS = ("name", "path", "fallback")

# Config options that can't be set per language.
_NOT_PER_LANGUAGE = ("languages", "site_dir", "INHERIT", "config_file_path")


@dataclasses.dataclass(eq=False)
class Language:
    """One language of a multi-language site (an item of `config.languages`)."""

    code: str
    """The language code, such as `en`, `zh` or `pt-BR`. Used as `lang` in HTML."""

    name: str
    """The name shown in the language switcher, such as `简体中文`."""

    default: bool = False
    """Whether this is the default language, built at the root of the site."""

    path: str = ""
    """Where this language is built, relative to the site root. Empty for the
    default language, the language code for the others unless set."""

    fallback: bool = True
    """Whether pages that have no translation are built from the default
    language's version. Always true for the default language."""

    overrides: dict[str, Any] = dataclasses.field(default_factory=dict, repr=False)
    """The config overrides for this language, as written in the config."""

    docs_dir: str = ""
    """The absolute path of the directory this language's pages are read from."""

    @property
    def locale(self) -> str:
        """The language code in the form theme locales use, such as `pt_BR`."""
        return self.code.replace("-", "_")


def parse_languages(value: object) -> list[Language]:
    """Validate the raw `languages` config value. Raises `ValueError`."""
    if isinstance(value, list):
        items: list[tuple[object, object]] = []
        for item in value:
            if isinstance(item, str):
                items.append((item, None))
            elif isinstance(item, dict) and len(item) == 1:
                items.append(next(iter(item.items())))
            else:
                raise ValueError(
                    f"Expected a language code or a mapping with one key, got: {item!r}"
                )
    elif isinstance(value, dict):
        items = list(value.items())
    else:
        raise ValueError(
            "Expected a mapping of language codes, such as {en: English, zh: 简体中文}."
        )
    if not items:
        raise ValueError("Expected at least one language.")

    languages: list[Language] = []
    seen_paths: set[str] = set()
    for index, (code, entry) in enumerate(items):
        if not isinstance(code, str) or not _CODE_RE.match(code):
            raise ValueError(
                f"'{code}' is not a language code. Use codes like 'en', 'zh' or 'pt-BR'."
            )
        if any(lang.code == code for lang in languages):
            raise ValueError(f"Language '{code}' is listed twice.")
        if entry is None:
            entry = {}
        elif isinstance(entry, str):
            entry = {"name": entry}
        elif not isinstance(entry, dict):
            raise ValueError(
                f"Language '{code}': expected a name or a mapping, got: {entry!r}"
            )
        overrides = {k: v for k, v in entry.items() if k not in _OWN_KEYS}
        for key in _NOT_PER_LANGUAGE:
            if key in overrides:
                raise ValueError(
                    f"Language '{code}': '{key}' can't be set per language."
                )

        name = entry.get("name", code)
        if not isinstance(name, str):
            raise ValueError(f"Language '{code}': 'name' must be a string.")
        fallback = entry.get("fallback", True)
        if not isinstance(fallback, bool):
            raise ValueError(f"Language '{code}': 'fallback' must be true or false.")
        default = index == 0
        if default:
            if "path" in entry:
                raise ValueError(
                    f"Language '{code}': the default language is built at the root of"
                    " the site, so it can't set 'path'."
                )
            path = ""
        else:
            path = entry.get("path", code)
            if (
                not isinstance(path, str)
                or not _PATH_RE.match(path.strip("/"))
                or any(part in (".", "..") for part in path.strip("/").split("/"))
            ):
                raise ValueError(
                    f"Language '{code}': 'path' must be a relative URL path, got: {path!r}"
                )
            path = path.strip("/")
            if path in seen_paths:
                raise ValueError(f"Language '{code}': path '{path}' is already used.")
            seen_paths.add(path)
        languages.append(
            Language(
                code=code,
                name=name,
                default=default,
                path=path,
                fallback=True if default else fallback,
                overrides=overrides,
            )
        )
    return languages


def current(config: MkDocsConfig) -> Language | None:
    """The language that `config` builds, or None for a single-language site."""
    languages = config.get("languages")
    if not languages:
        return None
    code = getattr(config, "_language_code", None)
    for lang in languages:
        if lang.code == code:
            return lang
    return languages[0]


def apply_language(config: MkDocsConfig, code: str | None) -> Language | None:
    """
    Apply the overrides of a language to a config that is loaded but not yet validated.

    `code` None selects the default language. Called by `load_config`.
    """
    raw = config.get("languages")
    if raw is None:
        if code is not None:
            raise exceptions.ConfigurationError(
                f"Can't build language '{code}': the config has no 'languages'."
            )
        return None
    try:
        languages = parse_languages(raw)
    except ValueError as e:
        raise exceptions.ConfigurationError(f"Config value 'languages': {e}")
    if code is None:
        lang = languages[0]
    else:
        found = [lang for lang in languages if lang.code == code]
        if not found:
            codes = ", ".join(lang.code for lang in languages)
            raise exceptions.ConfigurationError(
                f"Unknown language '{code}'. The config has: {codes}."
            )
        lang = found[0]

    config._language_code = lang.code
    config._base_docs_dir = config.get("docs_dir")
    overrides = lang.overrides
    theme_override = overrides.get("theme")
    theme = config.get("theme")
    if theme is None:
        theme = {"name": "mkdocs"}
    elif isinstance(theme, str):
        theme = {"name": theme}
    if isinstance(theme, dict):
        if isinstance(theme_override, str):
            theme = {"name": theme_override}
        elif isinstance(theme_override, dict):
            theme = _deep_merge(dict(theme), theme_override)
        # Material for MkDocs names its language `language`, with the code as
        # it is (`pt-BR`), instead of `locale`.
        keys = {"locale": lang.locale}
        if theme.get("name") == "material":
            keys["language"] = lang.code
        for key, value in keys.items():
            sets_key = isinstance(theme_override, dict) and key in theme_override
            if not sets_key and (not lang.default or key not in theme):
                theme[key] = value
    _deep_merge(config, {k: v for k, v in overrides.items() if k != "theme"})
    if isinstance(theme, dict):
        config["theme"] = theme
    return lang


def place_language(config: MkDocsConfig, lang: Language) -> None:
    """Move the build of a non-default language into its sub-directory of the site."""
    if lang.default:
        return
    config["site_dir"] = os.path.join(config.get("site_dir") or "site", lang.path)
    site_url = config.get("site_url")
    if site_url and "site_url" not in lang.overrides:
        config["site_url"] = language_site_url(site_url, lang)


def language_site_url(root_url: str, lang: Language) -> str:
    """The URL of a language's home page, given the site's root URL."""
    if lang.default:
        return root_url
    if not root_url.endswith("/"):
        root_url += "/"
    return urljoin(root_url, lang.path + "/")


def resolve_docs_dirs(config: MkDocsConfig, languages: list[Language]) -> None:
    """Set `docs_dir` of each language to an absolute path. Called after validation."""
    config_dir = os.path.dirname(config.config_file_path or "")
    if getattr(config, "_language_code", None) is None:
        # Not loaded through `load_config`, so no overrides were applied.
        base = config["docs_dir"]
    else:
        base = getattr(config, "_base_docs_dir", None) or "docs"
    # Languages without a `docs_dir` of their own share the default language's.
    base = languages[0].overrides.get("docs_dir", base)
    for lang in languages:
        docs_dir = os.fspath(lang.overrides.get("docs_dir", base))
        if not os.path.isabs(docs_dir):
            docs_dir = os.path.join(config_dir, docs_dir)
        lang.docs_dir = os.path.abspath(docs_dir)


def load_language_config(config: MkDocsConfig, code: str) -> MkDocsConfig:
    """Load the config of another language of the same site, from the same source."""
    source = getattr(config, "_source", None)
    if source is None:
        raise exceptions.ConfigurationError(
            "The config of other languages can only be loaded when the config was"
            " loaded with `mkdocs.config.load_config`."
        )
    data, name, kwargs = source
    from mkdocs.config.base import load_config

    fd = io.BytesIO(data)
    if name is not None:
        fd.name = name  # type: ignore[misc]
    return load_config(
        fd, config_file_path=config.config_file_path, _language=code, **kwargs
    )


# --- Finding the pages of a language ----------------------------------------


def _split_suffix(rel_path: str, codes: Iterable[str]) -> tuple[str, str | None]:
    """`guide/intro.zh.md` -> (`guide/intro.md`, `zh`) if `zh` is a language code."""
    head, filename = posixpath.split(rel_path)
    stem, ext = posixpath.splitext(filename)
    base, dot, suffix = stem.rpartition(".")
    if dot and base and suffix in codes:
        return posixpath.join(head, base + ext), suffix
    return rel_path, None


@dataclasses.dataclass
class SourceFile:
    src_uri: str
    """The path the file has in this language's build."""
    src_dir: str
    abs_src_path: str
    is_fallback: bool
    """Taken from the default language, because this language has no version of it."""


def select_sources(
    config: MkDocsConfig,
    lang: Language,
    walk: Callable[[str], Iterator[str]],
) -> list[SourceFile]:
    """
    Choose the source files of one language.

    `walk(dir)` yields the '/'-separated paths of the files in `dir`, relative to it.
    """
    languages: list[Language] = config["languages"]
    codes = {other.code for other in languages}
    default = languages[0]
    own_dir = lang.docs_dir
    shares_dir = os.path.normcase(default.docs_dir) == os.path.normcase(own_dir)
    dirs = [(own_dir, True)]
    if not lang.default and not shares_dir:
        dirs.append((default.docs_dir, False))

    chosen: dict[str, tuple[int, SourceFile]] = {}
    for src_dir, own in dirs:
        for rel_path in walk(src_dir):
            uri, code = _split_suffix(rel_path, codes)
            if code is not None and code != lang.code:
                continue  # Another language's version of a file.
            is_page = utils.is_markdown_file(uri)
            # A translation beats the untranslated file, own files beat the default's.
            rank = (2 if own else 0) + (1 if code is not None else 0)
            # An untranslated page of the default language.
            is_fallback = (
                is_page
                and code is None
                and not lang.default
                and (shares_dir or not own)
            )
            if is_fallback and not lang.fallback:
                continue
            prev = chosen.get(uri)
            if prev is None or prev[0] < rank:
                chosen[uri] = (
                    rank,
                    SourceFile(
                        uri,
                        src_dir,
                        os.path.normpath(os.path.join(src_dir, rel_path)),
                        is_fallback,
                    ),
                )
    return [source for _, source in chosen.values()]


def _walk_names(src_dir: str, skipped: set[str]) -> Iterator[str]:
    for source_dir, dirnames, filenames in os.walk(src_dir, followlinks=True):
        relative_dir = os.path.relpath(source_dir, src_dir)
        dirnames[:] = sorted(
            d for d in dirnames if os.path.join(source_dir, d) not in skipped
        )
        for filename in filenames:
            if os.path.join(source_dir, filename) in skipped:
                continue
            yield posixpath.normpath(
                posixpath.join(relative_dir.replace(os.sep, "/"), filename)
            )


def docs_dirs(config: MkDocsConfig) -> set[str]:
    """
    The docs directories of all languages.

    When one is inside another, its files belong only to its own language.
    (A walk doesn't skip the directory it starts from.)
    """
    return {os.path.abspath(lang.docs_dir) for lang in config["languages"]}


# --- The language switcher ----------------------------------------------------


def _link(from_path: str, to_path: str, url: str) -> str:
    """A link from the root of one language to `url` in another, both roots relative to the site."""
    if url in (".", "./"):
        url = ""
    if from_path == to_path:
        return url or "./"
    target = f"{to_path}/{url}" if to_path else url
    up = "../" * (from_path.count("/") + 1) if from_path else ""
    return up + target or "./"


class Switcher:
    """Works out where the language switcher of each page links to."""

    def __init__(self, config: MkDocsConfig) -> None:
        self.config = config
        self.languages: list[Language] = config["languages"]
        lang = current(config)
        assert lang is not None
        self.language = lang
        self._pages: dict[str, set[str]] = {}
        self.auto_alternate = "alternate" not in (config.get("extra") or {})

    def pages_of(self, lang: Language) -> set[str]:
        """The `src_uri` of every Markdown page of a language, as found on disk."""
        pages = self._pages.get(lang.code)
        if pages is None:
            skipped = docs_dirs(self.config)
            pages = self._pages[lang.code] = {
                source.src_uri
                for source in select_sources(
                    self.config, lang, lambda d: _walk_names(d, skipped)
                )
                if utils.is_markdown_file(source.src_uri)
            }
        return pages

    def context(self, page: Page | None) -> dict[str, Any]:
        """The `i18n` template variable for a page, or for a template that isn't a page."""
        file: File | None = page.file if page is not None else None
        url = page.url if page is not None else ""
        own_pages = self.pages_of(self.language)
        known = file is not None and file.src_uri in own_pages
        languages = []
        for lang in self.languages:
            available = file is not None and (
                not known
                or lang is self.language
                or file.src_uri in self.pages_of(lang)
            )
            link = _link(self.language.path, lang.path, url if available else "")
            site_url = self.config.get("site_url")
            languages.append(
                {
                    "code": lang.code,
                    "name": lang.name,
                    "lang": lang.code,
                    "link": link,
                    "url": urljoin(site_url, link) if site_url else None,
                    "current": lang is self.language,
                    "available": available or file is None,
                }
            )
        return {
            "language": {
                "code": self.language.code,
                "name": self.language.name,
                "path": self.language.path,
                "default": self.language.default,
            },
            "default_language": self.languages[0].code,
            "fallback": bool(
                file is not None and getattr(file, "language_fallback", False)
            ),
            "languages": languages,
        }

    def alternate(self, context: dict[str, Any]) -> list[dict[str, str]]:
        """`extra.alternate` in the form themes such as Material and Sumi read it."""
        return [
            {"name": item["name"], "link": item["link"], "lang": item["lang"]}
            for item in context["languages"]
        ]

"""
Reuse Markdown conversions between the rebuilds of `mkdocs serve`.

Each rebuild converts every page from Markdown to HTML again, although usually
only one file changed. The conversion of a page only depends on its Markdown
(after the `on_page_markdown` events), the Markdown extensions and their
config, the page's own URL, and the files that its links point to. When none
of those changed, the HTML of the previous rebuild is reused. Adding, removing
or renaming a page only converts again the pages whose links resolve
differently because of it.

Plugin events still run for every page, with the same values as before. The
cache is only used when every Markdown extension is known not to depend on
anything else (such as other files) or keep state outside the conversion: it is
on `SAFE_EXTENSIONS`, or it sets `mkdocs_cacheable = True` on its module or its
Extension class. Sites with other extensions, like those that `mkdocstrings` or
`mkdocs-autorefs` add, convert every page as before.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import datetime
import enum
import importlib
import logging
import os
import zlib
from typing import TYPE_CHECKING, Any

import jinja2

import mkdocs

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.files import File, Files
    from mkdocs.structure.pages import Page


log = logging.getLogger(__name__)


# Extensions whose output depends only on the Markdown text and their config.
# Notably absent: `pymdownx.snippets` and `pymdownx.b64`, which read other files.
SAFE_EXTENSIONS = frozenset(
    [
        f"markdown.extensions.{name}"
        for name in (
            "abbr",
            "admonition",
            "attr_list",
            "codehilite",
            "def_list",
            "extra",
            "fenced_code",
            "footnotes",
            "legacy_attrs",
            "legacy_em",
            "md_in_html",
            "meta",
            "nl2br",
            "sane_lists",
            "smarty",
            "tables",
            "toc",
            "wikilinks",
        )
    ]
    + [
        f"pymdownx.{name}"
        for name in (
            "arithmatex",
            "betterem",
            "caret",
            "critic",
            "details",
            "emoji",
            "escapeall",
            "extra",
            "fancylists",
            "highlight",
            "inlinehilite",
            "keys",
            "magiclink",
            "mark",
            "pathconverter",
            "progressbar",
            "saneheaders",
            "smartsymbols",
            "striphtml",
            "superfences",
            "tabbed",
            "tasklist",
            "tilde",
            "blocks.admonition",
            "blocks.caption",
            "blocks.definition",
            "blocks.details",
            "blocks.html",
            "blocks.tab",
        )
    ]
    + ["material.extensions.emoji", "mkdocs_sumi.markdown.extension"]
)

# An extension declares itself safe to cache by setting this attribute to True,
# on its module (when it is loaded by module name) or on its Extension class.
CACHEABLE_ATTR = "mkdocs_cacheable"


def _extension_name(ext: object) -> str | None:
    if not isinstance(ext, str):
        return None  # An extension instance a plugin added: unknown.
    name = ext.partition(":")[0]
    if "." not in name:
        name = f"markdown.extensions.{name}"
    return name


def _is_cacheable(ext: object) -> bool:
    """Whether the conversion with this extension depends only on the Markdown and config."""
    if not isinstance(ext, str):
        return getattr(type(ext), CACHEABLE_ATTR, False) is True
    if _extension_name(ext) in SAFE_EXTENSIONS:
        return True
    module_name, _, class_name = ext.partition(":")
    try:
        # Python-Markdown imports the same module to load the extension.
        module = importlib.import_module(module_name)
        target = getattr(module, class_name) if class_name else module
    except Exception:
        return False
    return getattr(target, CACHEABLE_ATTR, False) is True


def _describe(value: Any) -> Any:
    """A stable description of a config value, naming functions by their path."""
    if isinstance(value, dict):
        return sorted((str(k), _describe(v)) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return [_describe(v) for v in value]
    if callable(value):
        return f"{getattr(value, '__module__', '?')}.{getattr(value, '__qualname__', repr(value))}"
    return repr(value)


def _describe_extension(ext: object) -> Any:
    if isinstance(ext, str):
        return _extension_name(ext)
    # An instance: its class and the config it was created with.
    get_configs = getattr(ext, "getConfigs", None)
    configs = get_configs() if callable(get_configs) else None
    return (f"{type(ext).__module__}.{type(ext).__qualname__}", _describe(configs))


class _CapturedLogs(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.NOTSET)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        if not any(r is record for r in self.records):
            self.records.append(record)


def _file_state(file: File | None) -> tuple[str, str] | None:
    """What a link's conversion uses of the file it points to."""
    if file is None:
        return None
    return (file.url, file.inclusion.name)


class _RecordingFiles:
    """
    Stands in for `Files` during a conversion, and remembers every lookup.

    A page's links are resolved with `get_file_from_path`, so the lookups and
    their results are everything the conversion used of the other files.
    """

    def __init__(self, files: Files) -> None:
        self._files = files
        self.lookups: dict[str, tuple[str, str] | None] = {}

    def get_file_from_path(self, path: str) -> File | None:
        file = self._files.get_file_from_path(path)
        self.lookups[path] = _file_state(file)
        return file

    def __getattr__(self, name: str) -> Any:
        return getattr(self._files, name)

    def __iter__(self):
        return iter(self._files)

    def __len__(self) -> int:
        return len(self._files)

    def __contains__(self, item) -> bool:
        return item in self._files


class _Unstable(Exception):
    """A value has no description that stays the same between rebuilds."""


_SCALARS = (str, int, float, bool, type(None))


def _stable(value: Any) -> Any:
    """
    A description of a template variable that is the same in two rebuilds
    exactly when the value is the same. Raises `_Unstable` for anything else.
    """
    from mkdocs.config.base import Config as BaseConfig
    from mkdocs.structure.files import File
    from mkdocs.structure.nav import Link, Section
    from mkdocs.structure.pages import Page
    from mkdocs.structure.toc import AnchorLink, TableOfContents
    from mkdocs.utils.templates import NavFragmentCache

    if isinstance(value, _SCALARS):
        return value
    if isinstance(value, (list, tuple)):
        return [_stable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return ("set", sorted(repr(_stable(v)) for v in value))
    if isinstance(value, dict):
        return ("dict", [(_stable(k), _stable(v)) for k, v in value.items()])
    # Items of the navigation: the navigation itself is described once per build.
    if isinstance(value, Page):
        return ("page", value.url)
    if isinstance(value, Section):
        return ("section", value.title)
    if isinstance(value, Link):
        return ("link", value.title, value.url)
    if isinstance(value, File):
        return ("file", value.src_uri, value.url, value.dest_uri, value.inclusion.name)
    if isinstance(value, TableOfContents):
        return ("toc", [_stable(item) for item in value])
    if isinstance(value, AnchorLink):
        return ("anchor", value.id, value.title, value.level, _stable(value.children))
    if isinstance(value, BaseConfig):
        return ("config", [(k, _stable(v)) for k, v in value.items()])
    if isinstance(value, (datetime.date, datetime.time)):
        return ("datetime", value.isoformat())
    if isinstance(value, enum.Enum):
        return ("enum", type(value).__qualname__, value.name)
    if type(value).__name__ == "Locale" and type(value).__module__ in (
        "babel.core",
        "mkdocs.utils.babel_stub",
    ):
        return ("locale", str(value))
    if isinstance(value, NavFragmentCache):
        return ("nav_fragment", value.enabled)
    if callable(value) and hasattr(value, "__qualname__"):
        # A function or class in the globals: assumed not to change while serving.
        return ("callable", getattr(value, "__module__", "?"), value.__qualname__)
    raise _Unstable(type(value).__qualname__)


def _describe_page(page: Page) -> Any:
    """Every attribute of the page being rendered, including ones plugins set."""
    items = []
    for name, value in sorted(vars(page).items()):
        if name == "_toc_tokens":
            continue  # The same as `toc`, which the cache sets without it.
        if name in ("previous_page", "next_page"):
            value = None if value is None else (value.url, value.title)
        items.append((name, _stable(value)))
    return (page.title, items)


def _describe_nav(nav: Navigation) -> Any:
    from mkdocs.structure.nav import Link, Section
    from mkdocs.structure.pages import Page

    def item(it) -> Any:
        if isinstance(it, Page):
            return ("page", it.title, it.url, _stable(it.meta), it.is_link)
        if isinstance(it, Section):
            return ("section", it.title, [item(c) for c in it.children])
        if isinstance(it, Link):
            return ("link", it.title, it.url)
        raise _Unstable(type(it).__qualname__)

    homepage = nav.homepage.url if nav.homepage is not None else None
    return ([item(it) for it in nav.items], homepage)


def _describe_config(config: MkDocsConfig) -> Any:
    items = []
    for key, value in config.items():
        if key in ("plugins", "hooks", "extra"):
            # Plugins and hooks are code; `extra` may change per page and is
            # described then.
            continue
        if key == "theme":
            value = (value.name, list(value.dirs), dict(value.items()))
        elif key == "markdown_extensions":
            value = repr([_describe_extension(ext) for ext in value])
        elif key == "mdx_configs":
            value = repr(_describe(value or {}))
        elif key == "config_file_path" and value:
            # The first load of `mkdocs serve` may give it relative to the cwd.
            value = os.path.abspath(value)
        items.append((key, _stable(value)))
    return items


def _describe_env(env: jinja2.Environment) -> Any:
    return [
        sorted((k, repr(_stable(v))) for k, v in mapping.items())
        for mapping in (env.globals, env.filters, env.tests)
    ]


def _template_state(path: str) -> tuple[int, int] | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


class _RecordingLoader(jinja2.BaseLoader):
    """Wraps the theme's loader and remembers which file each template came from."""

    def __init__(self, loader: jinja2.BaseLoader, seen: dict) -> None:
        self.loader = loader
        self.seen = seen

    def get_source(self, environment, template):
        source, filename, uptodate = self.loader.get_source(environment, template)
        if filename is not None:
            self.seen[template] = (filename, _template_state(filename))
        else:
            self.seen[template] = None
        return source, filename, uptodate

    def list_templates(self):
        return self.loader.list_templates()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.loader, name)


class PageHTML:
    """The theme's HTML of a page, kept compressed: it holds the whole navigation."""

    def __init__(self, html: str) -> None:
        from mkdocs.utils import output

        data = html.encode("utf-8", errors="xmlcharrefreplace")
        # What `mkdocs.utils.output` compares, to leave the file alone.
        self.digest = output._digest(data)
        self._data = zlib.compress(data, 1)

    @property
    def html(self) -> str:
        return zlib.decompress(self._data).decode("utf-8")


@dataclasses.dataclass
class _Entry:
    content: str
    toc_tokens: list
    title: str | None
    present_anchor_ids: set[str]
    links_to_anchors: dict[str, dict[str, str]] | None
    logs: list[logging.LogRecord]
    # The paths the links were looked up with, and what was found there.
    lookups: dict[str, tuple[str, str] | None]

    def still_valid(self, files: Files) -> bool:
        get = files.get_file_from_path
        return all(
            _file_state(get(path)) == state for path, state in self.lookups.items()
        )


class RenderCache:
    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._used: set[str] = set()
        # Other results that only depend on their key, kept for one rebuild.
        self._memo: dict[Any, Any] = {}
        self._memo_used: dict[Any, Any] = {}
        self._build_key: tuple[int, str | None] | None = None
        # The rendered HTML of pages, by a digest of their template context.
        self._pages: dict[str, PageHTML] = {}
        self._pages_used: set[str] = set()
        # Template name -> the file it was loaded from and its (mtime, size).
        self._templates: dict[str, tuple[str, tuple[int, int] | None] | None] = {}
        self._loader: _RecordingLoader | None = None
        self._page_key: tuple[tuple[int, int, int], str | None] | None = None

    def start_build(self) -> None:
        """Forget entries that the previous build didn't use."""
        if self._used:
            self._entries = {k: v for k, v in self._entries.items() if k in self._used}
        self._used = set()
        if self._pages_used:
            self._pages = {
                k: v for k, v in self._pages.items() if k in self._pages_used
            }
        self._pages_used = set()
        self._loader = None
        self._page_key = None
        if self._memo_used:
            self._memo = self._memo_used
        self._memo_used = {}
        self._build_key = None

    def _context(self, config: MkDocsConfig) -> str | None:
        """What every page's conversion depends on in this build, or None if unsafe."""
        if self._build_key is not None and self._build_key[0] == id(config):
            return self._build_key[1]
        result: str | None = None
        if all(_is_cacheable(ext) for ext in config.markdown_extensions):
            names = [_describe_extension(ext) for ext in config.markdown_extensions]
            parts = [
                mkdocs.__version__,
                repr(names),
                repr(_describe(config.mdx_configs or {})),
                repr(config.use_directory_urls),
                repr(_describe(dict(config.validation))),
            ]
            result = hashlib.sha256("\0".join(parts).encode()).hexdigest()
        self._build_key = (id(config), result)
        return result

    def memo(self, key: Any, compute: Callable[[], Any]) -> Any:
        """
        The result of `compute()`, reused from the previous rebuild when `key`
        was the same. The key must describe everything the result depends on.
        """
        try:
            value = self._memo_used[key]
        except KeyError:
            try:
                value = self._memo[key]
            except KeyError:
                value = compute()
            self._memo_used[key] = value
        return value

    def watch_templates(self, env: jinja2.Environment, dirs: list[str]) -> None:
        """
        Note which template files `env` loads in this build. Forget the HTML of
        all pages if a template file that an earlier build used has changed,
        or another file now takes its place.
        """
        for name, entry in self._templates.items():
            path = None
            for d in dirs:
                candidate = os.path.join(d, *name.split("/"))
                if os.path.isfile(candidate):
                    path = candidate
                    break
            now = None if path is None else (path, _template_state(path))
            if now != entry:
                self._pages.clear()
                self._templates.clear()
                break
        if env.loader is not None:
            self._loader = env.loader = _RecordingLoader(env.loader, self._templates)

    def _page_context(
        self, config: MkDocsConfig, env: jinja2.Environment, nav: Navigation, pages
    ) -> str | None:
        """What every page's HTML depends on in this build, or None if unknown."""
        ids = (id(config), id(env), id(nav))
        if self._page_key is not None and self._page_key[0] == ids:
            return self._page_key[1]
        result: str | None = None
        # A plugin replaced the loader: the template files aren't known.
        if self._loader is not None and env.loader is self._loader:
            try:
                parts = (
                    mkdocs.__version__,
                    _describe_config(config),
                    _describe_env(env),
                    _describe_nav(nav),
                    _stable(pages),
                )
                result = hashlib.sha256(repr(parts).encode()).hexdigest()
            except _Unstable as e:
                log.debug(f"Not reusing page HTML in this build: {e} in the context")
        self._page_key = (ids, result)
        return result

    def page_key(
        self,
        page: Page,
        context: Mapping[str, Any],
        template: jinja2.Template,
        env: jinja2.Environment,
    ) -> str | None:
        """
        A digest of everything the theme's HTML of `page` depends on, or None
        when the context holds something without a stable description.
        """
        context = dict(context)
        config = context.pop("config", None)
        nav = context.pop("nav", None)
        pages = context.pop("pages", None)
        context.pop("page", None)
        build = (
            self._page_context(config, env, nav, pages)
            if config is not None and nav is not None
            else None
        )
        if build is None:
            return None
        try:
            parts = (
                template.name,
                _describe_page(page),
                _stable(context),
                _stable(config.extra),
            )
        except _Unstable as e:
            log.debug(f"Rendering '{page.file.src_uri}' again: {e} in its context")
            return None
        key = hashlib.sha256(f"{build}\0{parts!r}".encode()).hexdigest()
        self._pages_used.add(key)
        return key

    def get_page(self, key: str) -> PageHTML | None:
        """The HTML of a page that the previous rebuild rendered with this key."""
        return self._pages.get(key)

    def set_page(self, key: str, html: str) -> None:
        self._pages[key] = PageHTML(html)

    def render(
        self,
        page: Page,
        config: MkDocsConfig,
        files: Files,
        convert: Callable[[Files], None],
    ) -> None:
        """
        Set the HTML and the other results of converting `page`.

        `convert(files)` converts the page, looking up the files that its links
        point to in `files`.
        """
        context = self._context(config)
        if context is None or page.markdown is None:
            convert(files)
            return
        file = page.file
        key = hashlib.sha256(
            f"{context}\0{file.src_uri}\0{file.url}\0{file.inclusion.name}\0"
            f"{page.markdown}".encode()
        ).hexdigest()
        self._used.add(key)

        entry = self._entries.get(key)
        if entry is None or not entry.still_valid(files):
            entry = self._entries[key] = self._record(page, files, convert)
        else:
            for record in entry.logs:
                logging.getLogger(record.name).handle(record)

        page.content = entry.content
        from mkdocs.structure.toc import get_toc

        page.toc = get_toc(copy.deepcopy(entry.toc_tokens))
        page._title_from_render = entry.title
        page.present_anchor_ids = set(entry.present_anchor_ids)
        if entry.links_to_anchors is not None:
            links = {}
            for src_uri, anchors in entry.links_to_anchors.items():
                target = files.get_file_from_path(src_uri)
                if target is not None:
                    links[target] = dict(anchors)
            page.links_to_anchors = links

    def _record(
        self, page: Page, files: Files, convert: Callable[[Files], None]
    ) -> _Entry:
        handler = _CapturedLogs()
        recording = _RecordingFiles(files)
        loggers = [logging.getLogger(), logging.getLogger("mkdocs")]
        for logger in loggers:
            logger.addHandler(handler)
        try:
            convert(recording)  # type: ignore[arg-type]
        finally:
            for logger in loggers:
                logger.removeHandler(handler)
        links = page.links_to_anchors
        assert page.content is not None
        return _Entry(
            content=page.content,
            toc_tokens=copy.deepcopy(page._toc_tokens),
            title=page._title_from_render,
            present_anchor_ids=set(page.present_anchor_ids or ()),
            links_to_anchors=(
                None
                if links is None
                else {f.src_uri: dict(anchors) for f, anchors in links.items()}
            ),
            logs=handler.records,
            lookups=recording.lookups,
        )


# Set by `mkdocs serve` for the duration of the server.
active: RenderCache | None = None

"""
Reuse Markdown conversions between the rebuilds of `mkdocs serve`.

Each rebuild converts every page from Markdown to HTML again, although usually
only one file changed. The conversion of a page only depends on its Markdown
(after the `on_page_markdown` events), the Markdown extensions and their
config, the page's own URL and the list of files it can link to. When none of
those changed, the HTML of the previous rebuild is reused.

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
import importlib
import logging
from typing import TYPE_CHECKING, Any

import mkdocs

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page


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


@dataclasses.dataclass
class _Entry:
    content: str
    toc_tokens: list
    title: str | None
    present_anchor_ids: set[str]
    links_to_anchors: dict[str, dict[str, str]] | None
    logs: list[logging.LogRecord]


class RenderCache:
    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._used: set[str] = set()
        self._build_key: tuple[int, int, str | None] | None = None

    def start_build(self) -> None:
        """Forget entries that the previous build didn't use."""
        if self._used:
            self._entries = {k: v for k, v in self._entries.items() if k in self._used}
        self._used = set()
        self._build_key = None

    def _context(self, config: MkDocsConfig, files: Files) -> str | None:
        """What every page's conversion depends on in this build, or None if unsafe."""
        cache_id = (id(config), len(files))
        if self._build_key is not None and self._build_key[:2] == cache_id:
            return self._build_key[2]
        result: str | None = None
        if all(_is_cacheable(ext) for ext in config.markdown_extensions):
            names = [_describe_extension(ext) for ext in config.markdown_extensions]
            parts = [
                mkdocs.__version__,
                repr(names),
                repr(_describe(config.mdx_configs or {})),
                repr(config.use_directory_urls),
                repr(_describe(dict(config.validation))),
                repr(
                    [
                        (f.src_uri, f.url, f.inclusion.name, f.is_documentation_page())
                        for f in files
                    ]
                ),
            ]
            result = hashlib.sha256("\0".join(parts).encode()).hexdigest()
        self._build_key = (cache_id[0], cache_id[1], result)
        return result

    def render(self, page: Page, config: MkDocsConfig, files: Files, convert) -> None:
        context = self._context(config, files)
        if context is None or page.markdown is None:
            convert()
            return
        key = hashlib.sha256(
            f"{context}\0{page.file.src_uri}\0{page.file.url}\0{page.markdown}".encode()
        ).hexdigest()
        self._used.add(key)

        entry = self._entries.get(key)
        if entry is None:
            entry = self._entries[key] = self._record(page, convert)
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
                file = files.get_file_from_path(src_uri)
                if file is not None:
                    links[file] = dict(anchors)
            page.links_to_anchors = links

    def _record(self, page: Page, convert) -> _Entry:
        handler = _CapturedLogs()
        loggers = [logging.getLogger(), logging.getLogger("mkdocs")]
        for logger in loggers:
            logger.addHandler(handler)
        try:
            convert()
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
        )


# Set by `mkdocs serve` for the duration of the server.
active: RenderCache | None = None

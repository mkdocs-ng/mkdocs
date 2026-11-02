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
import importlib
import logging
from typing import TYPE_CHECKING, Any

import mkdocs

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File, Files
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

    def start_build(self) -> None:
        """Forget entries that the previous build didn't use."""
        if self._used:
            self._entries = {k: v for k, v in self._entries.items() if k in self._used}
        self._used = set()
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

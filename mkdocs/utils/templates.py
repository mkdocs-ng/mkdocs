from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence
    import datetime

from markupsafe import Markup

try:
    from jinja2 import pass_context as contextfilter  # type: ignore
except ImportError:  # pragma: no cover - Jinja2 < 3.0
    from jinja2 import contextfilter  # type: ignore

from jinja2 import pass_context

from mkdocs.utils import _get_norm_url, _norm_parts, normalize_url

if TYPE_CHECKING:
    from mkdocs.config.config_options import ExtraScriptValue
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page


class TemplateContext(TypedDict):
    nav: Navigation
    pages: Sequence[File]
    base_url: str
    extra_css: Sequence[str]  # Do not use, prefer `config.extra_css`.
    extra_javascript: Sequence[str]  # Do not use, prefer `config.extra_javascript`.
    mkdocs_version: str
    build_date_utc: datetime.datetime
    config: MkDocsConfig
    page: Page | None


@contextfilter
def url_filter(context: TemplateContext, value: str) -> str:
    """A Template filter to normalize URLs."""
    env = getattr(context, "environment", None)
    cache = getattr(env, "_mkdocs_nav_fragments", None)
    if cache is not None and cache.recording:
        return cache.url_token(str(value))
    return normalize_url(str(value), page=context["page"], base=context["base_url"])


_URL_TOKEN_RE = re.compile("\x00mkdocs-url:([0-9]+)\x00")


class NavFragmentCache:
    """
    Render each part of the navigation once per build instead of once per page.

    Every page of a site shows the whole navigation, so rendering it costs time
    proportional to the number of pages, on every page. But a nav section that
    doesn't contain the current page renders the same on every page, except for
    its URLs, which are relative to the page.

    Themes opt in by wrapping the markup of a nav item in a call block:

        {% call nav_fragment(nav_item) %} ... {% endcall %}

    The first time an inactive item is rendered, its markup is stored with
    placeholders in place of the URLs that went through the `url` filter. Later
    pages reuse that markup and only fill in their own relative URLs. Items that
    contain the current page are always rendered normally.

    The markup inside the block must depend only on the item, never on `page`
    (other than through the `url` filter), as it is shared between pages. Pass
    anything else the markup depends on as extra arguments: they become part of
    the cache key.
    """

    enabled: bool = True
    """Set to `False` to render every nav item on every page again."""

    def __init__(self) -> None:
        self.recording = 0
        self._fragments: dict[tuple, _Fragment] = {}
        self._urls: list[str] = []
        self._url_ids: dict[str, int] = {}
        self._has_alias: dict[int, tuple[Any, bool]] = {}
        self._nav: Any = None

    def clear(self) -> None:
        """Forget all recorded markup, such as after changing nav items mid-build."""
        self._fragments.clear()
        self._has_alias.clear()

    def url_token(self, url: str) -> str:
        index = self._url_ids.get(url)
        if index is None:
            index = self._url_ids[url] = len(self._urls)
            self._urls.append(url)
        return f"\x00mkdocs-url:{index}\x00"

    def _contains_alias(self, item) -> bool:
        # A repeated nav entry follows the active state of its page, which lives
        # elsewhere in the nav, so a section containing one may still change.
        entry = self._has_alias.get(id(item))
        if entry is None or entry[0] is not item:
            from mkdocs.structure.nav import PageAlias

            result = isinstance(item, PageAlias) or any(
                self._contains_alias(child) for child in (item.children or ())
            )
            entry = self._has_alias[id(item)] = (item, result)
        return entry[1]

    @pass_context
    def __call__(self, context, item, *key, caller) -> str:
        nav = context.get("nav")
        if nav is not self._nav:
            # A plugin may hand each page its own nav: start over.
            self._nav = nav
            self.clear()

        if (
            not self.enabled
            or getattr(item, "active", False)
            or self._contains_alias(item)
        ):
            return caller()

        # The same item may be rendered by different blocks, with different
        # markup: tell them apart by the code of the block.
        code = getattr(getattr(caller, "_func", None), "__code__", None)
        cache_key = (code, id(item), *key)
        fragment = self._fragments.get(cache_key)
        if fragment is None or fragment.item is not item:
            self.recording += 1
            try:
                html = caller()
            finally:
                self.recording -= 1
            fragment = self._fragments[cache_key] = _Fragment(item, html, self._urls)

        if self.recording:
            # Part of a bigger fragment that is being recorded: the outermost
            # fragment fills in the URLs.
            return fragment.html
        result = fragment.render(context["page"], context["base_url"])
        return Markup(result) if isinstance(fragment.html, Markup) else result


class _Fragment:
    """The recorded markup of a nav item, with placeholders for its URLs."""

    def __init__(self, item: Any, html: str, urls: list[str]) -> None:
        # Keep a reference to the item, so that its id can't be reused.
        self.item = item
        self.html = html
        pieces = _URL_TOKEN_RE.split(html)
        self.texts = pieces[0::2]
        self.urls = [urls[int(i)] for i in pieces[1::2]]
        self._prefix: list[str] | None = None
        self._by_depth: dict[int, str] = {}

        # Most nav sections hold pages from one directory. Then, from any page
        # outside that directory, all its URLs start with the same "../" steps,
        # and the rest is the same for every such page. Find that directory.
        if "\x01" in html:
            return
        parts = []
        for url in self.urls:
            path, level = _get_norm_url(url)
            if level != 0:
                return
            parts.append(_norm_parts(path))
        if parts:
            prefix = parts[0]
            for p in parts[1:]:
                common = 0
                for a, b in zip(prefix, p, strict=False):
                    if a != b:
                        break
                    common += 1
                prefix = prefix[:common]
            self._prefix = prefix
            self._parts = parts

    def render(self, page: Page | None, base: str) -> str:
        if not self.urls:
            return self.html
        if page is not None and self._prefix:
            # Same as `get_relative_url`: a last component with a dot is a file.
            other = page.url
            dirname, _, basename = other.rpartition("/")
            if "." in basename:
                other = dirname
            other_parts = _norm_parts(other)
            common = 0
            for a, b in zip(other_parts, self._prefix, strict=False):
                if a != b:
                    break
                common += 1
            if common < len(self._prefix):
                return self._for_depth(common).replace(
                    "\x01", "../" * (len(other_parts) - common)
                )
        texts, urls = self.texts, self.urls
        out = [texts[0]]
        for i, url in enumerate(urls):
            out.append(normalize_url(url, page=page, base=base))
            out.append(texts[i + 1])
        return "".join(out)

    def _for_depth(self, common: int) -> str:
        # The markup for pages that share `common` leading directories with
        # every URL here, with "\x01" where the "../" steps go.
        html = self._by_depth.get(common)
        if html is None:
            out = [self.texts[0]]
            for i, (url, parts) in enumerate(zip(self.urls, self._parts, strict=True)):
                path = _get_norm_url(url)[0]
                rel = "/".join(parts[common:])
                out.append("\x01" + (rel + "/" if path.endswith("/") else rel))
                out.append(self.texts[i + 1])
            html = self._by_depth[common] = "".join(out)
        return html


@contextfilter
def script_tag_filter(context: TemplateContext, extra_script: ExtraScriptValue) -> str:
    """Converts an ExtraScript value to an HTML <script> tag line."""
    html = '<script src="{0}"'
    if not isinstance(extra_script, str):
        if extra_script.type:
            html += ' type="{1.type}"'
        if extra_script.defer:
            html += " defer"
        if extra_script.async_:
            html += " async"
    html += "></script>"
    return Markup(html).format(url_filter(context, str(extra_script)), extra_script)

"""
Generate an `/llms.txt` file and Markdown versions of pages for LLMs.

See <https://llmstxt.org/>.
"""

from __future__ import annotations

import os
import posixpath
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin

from mkdocs import utils
from mkdocs.config import base
from mkdocs.config import config_options as c
from mkdocs.plugins import BasePlugin
from mkdocs.structure.nav import Section
from mkdocs.structure.pages import Page

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure import StructureItem
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation


class _PluginConfig(base.Config):
    full_output = c.Type(bool, default=False)


class LlmsTxtPlugin(BasePlugin[_PluginConfig]):
    """
    Publish the site's content for LLMs, following the llms.txt proposal.

    Writes a Markdown version of every page to the site, at the page's source
    path (e.g. `about.md`), and an `llms.txt` index at the site root that links
    to them, grouped by navigation section. With `full_output`, also writes
    `llms-full.txt` with the content of all pages in navigation order.
    """

    def on_nav(self, nav: Navigation, *, config: MkDocsConfig, files: Files) -> None:
        self._nav = nav

    def on_page_content(
        self, html: str, *, page: Page, config: MkDocsConfig, files: Files
    ) -> None:
        if not page.file.inclusion.is_excluded():
            utils.write_file(
                page_markdown(page).encode("utf-8"),
                os.path.join(config.site_dir, markdown_path(page)),
            )

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        pages = [p for p in self._nav.pages if not p.file.inclusion.is_excluded()]
        utils.write_file(
            llms_txt(self._nav.items, config).encode("utf-8"),
            os.path.join(config.site_dir, "llms.txt"),
        )
        if self.config.full_output:
            # With `--dirty`, pages that weren't rebuilt have no Markdown.
            content = "\n".join(
                page_markdown(p) for p in pages if p.markdown is not None
            )
            utils.write_file(
                (_header(config) + content).encode("utf-8"),
                os.path.join(config.site_dir, "llms-full.txt"),
            )


def markdown_path(page: Page) -> str:
    """The path of a page's Markdown version, relative to the site root."""
    return posixpath.splitext(page.file.src_uri)[0] + ".md"


def page_markdown(page: Page) -> str:
    """The page's Markdown as processed by plugins, starting with its title."""
    markdown = page.markdown or ""
    if page.content_title is None and page.title:
        # The page has no top-level heading of its own: its title comes from
        # the nav, its metadata or its file name.
        markdown = f"# {page.title}\n\n{markdown}"
    return markdown.strip() + "\n"


def llms_txt(items: list[StructureItem], config: MkDocsConfig) -> str:
    """Build the llms.txt index, with one list of links per nav section."""
    sections: dict[str, list[str]] = {}

    def add_items(items: list[StructureItem], path: tuple[str, ...]) -> None:
        for item in items:
            if isinstance(item, Section):
                add_items(item.children, (*path, item.title))
            elif isinstance(item, Page) and not item.file.inclusion.is_excluded():
                heading = " / ".join(path) or "Pages"
                sections.setdefault(heading, []).append(_link(item, config))

    add_items(items, ())
    output = _header(config)
    for heading, links in sections.items():
        output += f"## {heading}\n\n" + "\n".join(links) + "\n\n"
    return output.rstrip("\n") + "\n"


def _header(config: MkDocsConfig) -> str:
    header = f"# {config.site_name}\n\n"
    if config.site_description:
        header += f"> {config.site_description}\n\n"
    return header


def _link(page: Page, config: MkDocsConfig) -> str:
    # The title is unknown if the page wasn't read, e.g. in a `--dirty` build.
    title = page.title or page.file.name
    title = title.replace("[", r"\[").replace("]", r"\]")
    url = quote(markdown_path(page))
    if config.site_url:
        url = urljoin(config.site_url, url)
    link = f"- [{title}]({url})"
    if description := page.meta.get("description"):
        link += ": " + " ".join(str(description).split())
    return link

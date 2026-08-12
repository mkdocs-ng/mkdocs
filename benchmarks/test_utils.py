"""Benchmarks for the utility helpers used throughout a build."""

from __future__ import annotations

from typing import TYPE_CHECKING

from benchmarks.corpus import make_markdown
from mkdocs.utils import (
    get_markdown_title,
    get_relative_url,
    meta,
    nest_paths,
    normalize_url,
)
from mkdocs.utils.rendering import _strip_tags

if TYPE_CHECKING:
    from mkdocs.structure.pages import Page

PATHS = [
    f"section-{s:02d}/{'sub/' * (s % 3)}page-{p:02d}.md"
    for s in range(10)
    for p in range(20)
]


def test_meta_get_data(benchmark) -> None:
    """Split the YAML front matter from the Markdown body of every page."""
    documents = [make_markdown(seed) for seed in range(20)]

    def parse_all() -> int:
        return sum(len(meta.get_data(doc)[1]) for doc in documents)

    assert benchmark(parse_all) > 0


def test_get_markdown_title(benchmark) -> None:
    """Extract the title from a Markdown document without rendering it."""
    document, _ = meta.get_data(make_markdown(3, headings=40))

    assert benchmark(get_markdown_title, document)


def test_get_relative_url(benchmark) -> None:
    """Compute relative URLs, done for every link of every page."""
    urls = [(a, b) for a in PATHS[:40] for b in PATHS[:10]]

    def relative_all() -> int:
        return sum(len(get_relative_url(url, other)) for url, other in urls)

    assert benchmark(relative_all) > 0


def test_normalize_url(benchmark) -> None:
    """Normalize the URLs used by the theme templates."""
    urls = [*PATHS, "https://example.com/", "#anchor", "/absolute/path"]

    def normalize_all() -> int:
        return sum(len(normalize_url(url)) for url in urls)

    assert benchmark(normalize_all) > 0


def test_nest_paths(benchmark) -> None:
    """Turn a flat list of source paths into the implicit navigation tree."""
    assert len(benchmark(nest_paths, PATHS)) > 0


def test_strip_tags(benchmark, rendered_pages: list[Page]) -> None:
    """Strip the HTML out of rendered content, as the search index does."""
    html = [page.content for page in rendered_pages]

    def strip_all() -> int:
        return sum(len(_strip_tags(content)) for content in html)

    assert benchmark(strip_all) > 0

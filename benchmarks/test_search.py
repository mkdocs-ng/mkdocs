"""Benchmarks for the built-in search plugin index generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mkdocs.contrib.search.search_index import ContentParser, SearchIndex

if TYPE_CHECKING:
    from mkdocs.structure.pages import Page

INDEX_CONFIG = dict(
    lang=["en"],
    separator=r"[\s\-]+",
    min_search_length=3,
    prebuild_index=False,
    indexing="full",
)


def test_search_index_add_entries(benchmark, rendered_pages: list[Page]) -> None:
    """Parse the HTML of every page and add its sections to the search index."""

    def index_all() -> SearchIndex:
        index = SearchIndex(**INDEX_CONFIG)
        for page in rendered_pages:
            index.add_entry_from_context(page)
        return index

    assert len(benchmark(index_all)._entries) > 0


def test_search_index_generate(benchmark, rendered_pages: list[Page]) -> None:
    """Serialize a fully populated search index to JSON."""
    index = SearchIndex(**INDEX_CONFIG)
    for page in rendered_pages:
        index.add_entry_from_context(page)

    assert len(benchmark(index.generate_search_index)) > 0


def test_content_parser(benchmark, rendered_pages: list[Page]) -> None:
    """Run the HTML parser that splits rendered pages into indexable sections."""
    html = [page.content for page in rendered_pages]

    def parse_all() -> int:
        sections = 0
        for content in html:
            parser = ContentParser()
            parser.feed(content)
            parser.close()
            sections += len(parser.data)
        return sections

    assert benchmark(parse_all) > 0

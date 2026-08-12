"""Search index generation benchmark."""

from __future__ import annotations

from mkdocs.contrib.search.search_index import SearchIndex


def test_search_index(benchmark, populated_site):
    """
    Index every page and serialize the search index.

    Covers the `HTMLParser` re-parse of each rendered page
    (`add_entry_from_context`) plus the final JSON serialization
    (`generate_search_index`), matching what the search plugin does during
    `on_page_context` and `on_post_build`.
    """
    cfg, files, nav, env = populated_site
    pages = [f.page for f in files.documentation_pages()]

    def run():
        index = SearchIndex(
            lang=["en"],
            separator=r"[\s\-]+",
            min_search_length=3,
            prebuild_index=False,
            indexing="full",
        )
        for page in pages:
            index.add_entry_from_context(page)
        return index.generate_search_index()

    assert benchmark(run)

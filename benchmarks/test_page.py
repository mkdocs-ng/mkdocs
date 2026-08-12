"""Per-page Markdown rendering benchmark."""

from __future__ import annotations


def test_page_markdown_render(benchmark, populated_site):
    """
    Isolated `Page.render()` for one representative page.

    `Page.render` constructs a fresh `markdown.Markdown` instance on every
    call (see `mkdocs/structure/pages.py`), so this measures extension
    setup + conversion + toc extraction — the dominant per-page cost of the
    populate pass.
    """
    cfg, files, nav, env = populated_site
    page = files.documentation_pages()[1].page
    assert page is not None

    benchmark(lambda: page.render(cfg, files))

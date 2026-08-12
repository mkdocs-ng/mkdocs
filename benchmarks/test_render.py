"""Theme template rendering benchmark."""

from __future__ import annotations

from mkdocs.commands.build import get_context


def test_template_render_large_nav(benchmark, populated_site):
    """
    One page's Jinja render, including `get_context`, with a large nav.

    Built-in themes iterate the full navigation for every page, which makes
    template rendering O(pages) per page — the O(N^2) sitewide term behind
    upstream issue mkdocs/mkdocs#3695.
    """
    cfg, files, nav, env = populated_site
    doc_files = files.documentation_pages()
    page = doc_files[len(doc_files) // 2].page
    assert page is not None
    page.active = True
    template = env.get_template("main.html")

    def run():
        context = get_context(nav, doc_files, cfg, page)
        return template.render(context)

    try:
        result = benchmark(run)
        assert result.strip()
    finally:
        page.active = False

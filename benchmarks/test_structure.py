"""Benchmarks for the file collection, navigation and page structures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import markdown

from benchmarks.corpus import make_markdown
from mkdocs.structure.files import File, get_files
from mkdocs.structure.nav import get_navigation
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files


def test_get_files(benchmark, config: MkDocsConfig) -> None:
    """Walk the docs directory and build the `Files` collection."""
    assert len(benchmark(get_files, config)) > 0


def test_get_navigation(benchmark, config: MkDocsConfig, files: Files) -> None:
    """Build the navigation tree out of the file collection."""
    assert len(benchmark(get_navigation, files, config).pages) > 0


def test_file_creation(benchmark, config: MkDocsConfig) -> None:
    """Instantiate `File` objects, which computes source/destination URIs."""
    paths = [f"section-{i % 5:02d}/page-{i:03d}.md" for i in range(500)]
    docs_dir = config.docs_dir
    site_dir = config.site_dir

    def create_files() -> int:
        return len([File(path, docs_dir, site_dir, True) for path in paths])

    assert benchmark(create_files) == len(paths)


def test_files_lookup(benchmark, files: Files) -> None:
    """Resolve source URIs against the file collection, as link resolution does."""
    uris = [file.src_uri for file in files]

    def lookup_all() -> int:
        found = 0
        for uri in uris:
            if files.get_file_from_path(uri) is not None:
                found += 1
        return found

    assert benchmark(lookup_all) == len(uris)


def test_page_render(benchmark, config: MkDocsConfig, files: Files) -> None:
    """Convert a single page from Markdown to HTML, including link resolution."""
    file = files.documentation_pages()[1]
    page = Page(None, file, config)
    page.read_source(config)

    benchmark(page.render, config, files)
    assert page.content


def test_page_render_large(benchmark, config: MkDocsConfig, files: Files) -> None:
    """Convert a much larger page, dominated by the Markdown conversion itself."""
    file = files.documentation_pages()[0]
    page = Page(None, file, config)
    page.markdown = make_markdown(42, headings=60)

    benchmark(page.render, config, files)
    assert page.content


def test_get_toc(benchmark) -> None:
    """Turn the Markdown `toc` tokens into MkDocs' table of contents objects."""
    md = markdown.Markdown(extensions=["toc"])
    md.convert(make_markdown(7, headings=60))
    toc_tokens = md.toc_tokens

    assert len(list(benchmark(get_toc, toc_tokens))) > 0

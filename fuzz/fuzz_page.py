"""
Fuzz the page pipeline: front matter, Markdown rendering and link rewriting.

This runs on every page of a site, so any exception it raises is a bug. Run it
with `pip install atheris -e .` and `python fuzz/fuzz_page.py -max_total_time=60`.
"""

from __future__ import annotations

import logging
import sys
import tempfile

import atheris

with atheris.instrument_imports():
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File, Files
    from mkdocs.structure.pages import Page
    from mkdocs.utils import meta

logging.disable(logging.CRITICAL)

_docs_dir = tempfile.mkdtemp()
config = MkDocsConfig()
config.load_dict({"site_name": "Fuzz", "docs_dir": _docs_dir, "plugins": []})
assert config.validate() == ([], [])


def _file(path: str) -> File:
    return File(path, config.docs_dir, config.site_dir, config.use_directory_urls)


# The fuzzed page, plus other files for its links to point at.
_page_file = _file("sub/fuzz.md")
files = Files(
    [_page_file]
    + [_file(p) for p in ("index.md", "other.md", "sub/page.md", "img/a.png")]
)


def test_one_input(data: bytes) -> None:
    text = atheris.FuzzedDataProvider(data).ConsumeUnicodeNoSurrogates(len(data))
    page = Page(None, _page_file, config)
    page.markdown, page.meta = meta.get_data(text)
    page.render(config, files)
    _ = page.title, page.toc


def main() -> None:
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

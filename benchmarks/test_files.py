"""File discovery and navigation construction benchmark."""

from __future__ import annotations

from conftest import SIZES

from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation


def test_get_files_and_nav(benchmark, site_factory, load_bench_config):
    """
    `get_files` (docs_dir walk) + `get_navigation` for the largest site.

    This runs at the start of every build — including every rebuild in the
    `mkdocs serve` loop.
    """
    cfg = load_bench_config(site_factory(max(SIZES)))

    def run():
        files = get_files(cfg)
        return get_navigation(files, cfg)

    benchmark(run)

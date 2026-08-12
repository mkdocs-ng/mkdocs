"""
Scaling benchmarks: how build cost grows with site size.

These complement the fixed-size suite by building the same deterministic
corpus at several sizes, plus two scenarios from the `mkdocs serve` loop.
The default sizes are modest so CI stays fast; override them locally for
larger scaling studies:

    MKDOCS_BENCH_SIZES=100,400,1600 hatch run bench:codspeed benchmarks/test_scaling.py
"""

from __future__ import annotations

import logging
import os

import pytest

from benchmarks.corpus import PAGES_PER_SECTION, write_site
from mkdocs.commands.build import _build_page, _populate_page, build
from mkdocs.config.base import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

SIZES = [int(s) for s in os.environ.get("MKDOCS_BENCH_SIZES", "10,50,200").split(",")]


@pytest.fixture(autouse=True, scope="module")
def _quiet_mkdocs_logging():
    """Dirty rebuilds legitimately log a warning; keep benchmark output clean."""
    logger = logging.getLogger("mkdocs")
    handler = logging.NullHandler()
    logger.addHandler(handler)
    old_level = logger.level
    logger.setLevel(logging.ERROR)
    yield
    logger.setLevel(old_level)
    logger.removeHandler(handler)


def _sections_for(n_pages: int) -> int:
    # Each section contributes an index page plus its regular pages, and the
    # site has one root index page on top.
    return max(1, round((n_pages - 1) / (PAGES_PER_SECTION + 1)))


@pytest.fixture(scope="module")
def sized_site_factory(tmp_path_factory):
    """Return ``get(n_pages) -> str`` (config file path), one site per size."""
    cache: dict[int, str] = {}

    def get(n_pages: int) -> str:
        if n_pages not in cache:
            root = tmp_path_factory.mktemp(f"scaling_site_{n_pages}")
            cache[n_pages] = write_site(str(root), sections=_sections_for(n_pages))
        return cache[n_pages]

    return get


@pytest.mark.parametrize("n_pages", SIZES)
def test_full_build_scaling(benchmark, sized_site_factory, tmp_path, n_pages) -> None:
    """Clean full build at increasing site sizes (upstream mkdocs/mkdocs#3695)."""
    config_file = sized_site_factory(n_pages)
    counter = iter(range(1000))

    def setup():
        site_dir = str(tmp_path / f"site-{next(counter)}")
        return (load_config(config_file, site_dir=site_dir),), {}

    benchmark.pedantic(build, setup=setup, rounds=1, warmup_rounds=0)


def test_dirty_rebuild(benchmark, sized_site_factory, tmp_path) -> None:
    """
    Proxy for the `mkdocs serve --dirty` inner loop (no file modified).

    Even with nothing changed, every rebuild re-walks the docs directory,
    rebuilds the navigation, recreates the Jinja environment and re-runs all
    plugin events.
    """
    config_file = sized_site_factory(SIZES[len(SIZES) // 2])
    site_dir = str(tmp_path / "site")
    build(load_config(config_file, site_dir=site_dir))

    def setup():
        return (load_config(config_file, site_dir=site_dir),), {"dirty": True}

    benchmark.pedantic(build, setup=setup, rounds=1, warmup_rounds=0)


def test_template_render_large_nav(benchmark, sized_site_factory, tmp_path) -> None:
    """
    Render a single page against the largest site's navigation.

    Built-in themes iterate the full navigation for every page, so template
    rendering costs O(pages) per page — the O(N^2) sitewide term behind
    upstream issue mkdocs/mkdocs#3695.
    """
    config = load_config(
        sized_site_factory(max(SIZES)), site_dir=str(tmp_path / "large-site")
    )
    config = config.plugins.on_config(config)
    config.plugins.on_pre_build(config=config)
    files = get_files(config)
    env = config.theme.get_env()
    files.add_files_from_theme(env, config)
    nav = get_navigation(files, config)
    doc_files = files.documentation_pages()
    file = doc_files[len(doc_files) // 2]
    assert file.page is not None
    _populate_page(file.page, config, files)
    env = config.plugins.on_env(env, config=config, files=files)

    def render_one() -> None:
        _build_page(file.page, config, doc_files, nav, env)

    benchmark(render_one)

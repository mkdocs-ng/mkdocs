"""End-to-end build pipeline benchmarks."""

from __future__ import annotations

import pytest
from conftest import SIZES

from mkdocs.commands import build


@pytest.mark.parametrize("n_pages", SIZES)
def test_full_build(benchmark, site_factory, load_bench_config, n_pages):
    """
    A clean full build, including config loading.

    Config loading is part of the measured region on purpose: the `mkdocs
    serve` rebuild loop re-loads the config before every build, and reusing a
    validated config across builds is unsafe anyway (plugin `on_config` hooks
    mutate it).
    """
    site = site_factory(n_pages)

    def run():
        cfg = load_bench_config(site)
        build.build(cfg)

    benchmark(run)


def test_dirty_rebuild(benchmark, site_factory, load_bench_config):
    """Proxy for the `mkdocs serve --dirty` inner loop (no file modified)."""
    site = site_factory(SIZES[len(SIZES) // 2])
    build.build(load_bench_config(site))

    def run():
        cfg = load_bench_config(site)
        build.build(cfg, dirty=True)

    benchmark(run)

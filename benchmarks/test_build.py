"""End-to-end benchmarks for a full site build."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mkdocs.commands.build import _build_page, _populate_page, build
from mkdocs.config.base import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation


def test_build_site(benchmark, config_file_path: str, tmp_path) -> None:
    """Full `mkdocs build` of the generated site: files, nav, render, templates."""
    counter = iter(range(1000))

    def setup():
        site_dir = str(tmp_path / f"site-{next(counter)}")
        return (load_config(config_file_path, site_dir=site_dir),), {}

    benchmark.pedantic(build, setup=setup, rounds=1, warmup_rounds=0)


def test_build_site_no_directory_urls(
    benchmark, config_file_path: str, tmp_path
) -> None:
    """Same build with `use_directory_urls` disabled, which changes URL resolution."""
    counter = iter(range(1000))

    def setup():
        site_dir = str(tmp_path / f"flat-site-{next(counter)}")
        config = load_config(
            config_file_path, site_dir=site_dir, use_directory_urls=False
        )
        return (config,), {}

    benchmark.pedantic(build, setup=setup, rounds=1, warmup_rounds=0)


def test_populate_pages(
    benchmark, config: MkDocsConfig, files: Files, navigation: Navigation
) -> None:
    """Read and convert the Markdown of every page, without writing any output."""

    def populate_all() -> int:
        for file in files.documentation_pages():
            assert file.page is not None
            _populate_page(file.page, config, files)
        return len(navigation.pages)

    assert benchmark(populate_all) > 0


def test_build_theme_pages(benchmark, config: MkDocsConfig) -> None:
    """Render the `mkdocs` theme templates and write the HTML of every page."""
    config = config.plugins.on_config(config)
    config.plugins.on_pre_build(config=config)

    files = get_files(config)
    env = config.theme.get_env()
    files.add_files_from_theme(env, config)
    nav = get_navigation(files, config)
    doc_files = files.documentation_pages()
    for file in doc_files:
        assert file.page is not None
        _populate_page(file.page, config, files)
    env = config.plugins.on_env(env, config=config, files=files)

    def build_all() -> None:
        for file in doc_files:
            assert file.page is not None
            _build_page(file.page, config, doc_files, nav, env)

    benchmark(build_all)

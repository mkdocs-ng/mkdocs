"""Shared fixtures for the MkDocs benchmark suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from benchmarks.corpus import write_site
from mkdocs.config.base import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page


@pytest.fixture(scope="session")
def config_file_path(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Generate the benchmark site on disk once for the whole session."""
    return write_site(str(tmp_path_factory.mktemp("mkdocs_bench_site")))


@pytest.fixture
def config(config_file_path: str, tmp_path) -> MkDocsConfig:
    """A freshly loaded and validated configuration for the generated site."""
    return load_config(config_file_path, site_dir=str(tmp_path / "site"))


@pytest.fixture
def files(config: MkDocsConfig) -> Files:
    return get_files(config)


@pytest.fixture
def navigation(config: MkDocsConfig, files: Files) -> Navigation:
    return get_navigation(files, config)


@pytest.fixture
def rendered_pages(
    config: MkDocsConfig, files: Files, navigation: Navigation
) -> list[Page]:
    """Every documentation page of the generated site, read and rendered."""
    for page in navigation.pages:
        page.read_source(config)
        page.render(config, files)
    return list(navigation.pages)

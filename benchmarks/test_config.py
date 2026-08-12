"""Benchmarks for configuration loading and validation."""

from __future__ import annotations

import io

from mkdocs.config.base import load_config
from mkdocs.utils import yaml as yaml_utils
from mkdocs.utils.yaml import yaml_load


def test_load_config(benchmark, config_file_path: str, tmp_path) -> None:
    """Read `mkdocs.yml`, apply the schema defaults and validate every option."""
    site_dir = str(tmp_path / "site")

    config = benchmark(load_config, config_file_path, site_dir=site_dir)
    assert config.site_name == "Benchmark Site"


def test_yaml_load(benchmark, config_file_path: str) -> None:
    """Parse the YAML configuration with MkDocs' loader (env tags, includes)."""
    with open(config_file_path, "rb") as f:
        raw = f.read()

    def load() -> dict:
        return yaml_load(io.BytesIO(raw))

    assert benchmark(load)["site_name"] == "Benchmark Site"


def test_get_yaml_loader(benchmark) -> None:
    """Build the YAML loader class, done for every config and every page."""
    assert benchmark(yaml_utils.get_yaml_loader) is not None

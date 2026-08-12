"""
Shared fixtures for the performance benchmark suite.

The benchmarks deliberately avoid importing anything from ``mkdocs.tests``:
that package installs a ``logging.lastResort`` handler which raises on any
WARNING-level record, and some benchmarks (e.g. dirty rebuilds) legitimately
log warnings.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import pytest

from mkdocs.config.defaults import MkDocsConfig

if TYPE_CHECKING:
    from pathlib import Path

# Synthetic site sizes (page counts) exercised by the full-build benchmarks.
# Override locally for scaling studies, e.g.:
#   MKDOCS_BENCH_SIZES=100,400,1600 pytest --codspeed benchmarks/test_build.py
SIZES = [int(s) for s in os.environ.get("MKDOCS_BENCH_SIZES", "10,50,200").split(",")]

PAGES_PER_SECTION = 10

_PARAGRAPH = (
    "MkDocs is a fast and simple static site generator that is geared towards "
    "building project documentation. Documentation source files are written in "
    "Markdown and configured with a single YAML configuration file. It can be "
    "extended with third-party themes, plugins, and Markdown extensions, and "
    "the built-in development server rebuilds the site while you edit."
)

_CODE_BLOCK = """\
```python
def build(config, *, dirty=False):
    \"\"\"Run the MkDocs build pipeline.\"\"\"
    for page in pages:
        page.render(config, files)
    return site_dir
```
"""


def _page_md(section: int, index: int) -> str:
    """A realistic documentation page: headings, prose, code and links."""
    prev_link = f"[previous page](page_{index - 1:02d}.md)" if index > 0 else ""
    next_link = "[usage notes](page_00.md#usage)"
    lines = [
        f"# Section {section} page {index}",
        "",
        _PARAGRAPH,
        "",
        f"Read the [home page](../index.md) first. {prev_link} {next_link}",
        "",
    ]
    for heading in ("Overview", "Configuration", "Usage", "Troubleshooting"):
        lines += [
            f"## {heading}",
            "",
            _PARAGRAPH,
            "",
            f"Use the `--{heading.lower()}` flag together with `mkdocs build`.",
            "",
        ]
    lines += [
        "### Example",
        "",
        _CODE_BLOCK,
        "",
        "* first item with `inline code`",
        "* second item with **strong emphasis**",
        "* third item with a [section link](#overview)",
        "",
    ]
    return "\n".join(lines)


def _make_site(root: Path, n_pages: int) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True)
    n_sections = (n_pages - 1 + PAGES_PER_SECTION - 1) // PAGES_PER_SECTION
    index_lines = ["# Benchmark Site", "", _PARAGRAPH, ""]
    index_lines += [
        f"* [Section {s}](section_{s:02d}/page_00.md)" for s in range(n_sections)
    ]
    (docs / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    for p in range(n_pages - 1):
        section, index = divmod(p, PAGES_PER_SECTION)
        page = docs / f"section_{section:02d}" / f"page_{index:02d}.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(_page_md(section, index), encoding="utf-8")


def _load_config(site_root: Path, **extra) -> MkDocsConfig:
    """
    Build and validate a config for a generated site.

    ``site_dir`` is a sibling of ``docs_dir`` so validation stays clean.
    """
    cfg = MkDocsConfig(config_file_path=str(site_root / "mkdocs.yml"))
    cfg.load_dict(
        {
            "site_name": "Benchmark Site",
            "docs_dir": str(site_root / "docs"),
            "site_dir": str(site_root / "site"),
            "plugins": ["search"],
            **extra,
        }
    )
    errors, warnings = cfg.validate()
    assert errors == [], errors
    assert warnings == [], warnings
    return cfg


@pytest.fixture(autouse=True, scope="session")
def _quiet_mkdocs_logging():
    logger = logging.getLogger("mkdocs")
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.ERROR)


@pytest.fixture(scope="session")
def load_bench_config():
    """Expose the config loader to test modules without importing conftest."""
    return _load_config


@pytest.fixture(scope="session")
def site_factory(tmp_path_factory):
    """Return ``get(n_pages) -> Path``, generating each site size once."""
    cache: dict[int, Path] = {}

    def get(n_pages: int) -> Path:
        if n_pages not in cache:
            root = tmp_path_factory.mktemp(f"bench_site_{n_pages}")
            _make_site(root, n_pages)
            cache[n_pages] = root
        return cache[n_pages]

    return get


@pytest.fixture(scope="session")
def populated_site(site_factory):
    """
    ``(config, files, nav, env)`` for the largest site, pages populated.

    Built once per session; consuming benchmarks must treat it as read-only.
    """
    from mkdocs.commands.build import _populate_page
    from mkdocs.structure.files import get_files
    from mkdocs.structure.nav import get_navigation
    from mkdocs.structure.pages import Page

    cfg = _load_config(site_factory(max(SIZES)))
    cfg = cfg.plugins.on_config(cfg)
    cfg.plugins.on_pre_build(config=cfg)
    files = get_files(cfg)
    env = cfg.theme.get_env()
    files.add_files_from_theme(env, cfg)
    files = cfg.plugins.on_files(files, config=cfg)
    nav = get_navigation(files, cfg)
    for file in files.documentation_pages():
        Page(None, file, cfg)
        assert file.page is not None
        _populate_page(file.page, cfg, files)
    return cfg, files, nav, env

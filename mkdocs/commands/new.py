from __future__ import annotations

import logging
import os

from mkdocs import utils

SCHEMA_COMMENT = "# yaml-language-server: $schema=https://mkdocs-ng.org/schema.json\n"

# The theme `mkdocs new` picks when none is given and Sumi is installed.
DEFAULT_THEME = "sumi"

# Themes that come from a separate package, and the package to install.
THEME_PACKAGES = {
    "sumi": "mkdocs-sumi",
    "material": "mkdocs-ng-material",
}

# Plugins a theme needs next to the ones every new project gets.
THEME_PLUGINS = {
    "sumi": ["sumi"],
}


def config_text(theme: str) -> str:
    """Return the `mkdocs.yml` of a new project that uses `theme`."""
    plugins = "".join(f"  - {name}\n" for name in THEME_PLUGINS.get(theme, []))
    return (
        SCHEMA_COMMENT
        + f"""site_name: My Docs

theme:
  name: {theme}

plugins:
  - search
  - llms_txt  # llms.txt and a Markdown copy of every page, for AI tools
{plugins}"""
    )


index_text = """# Welcome to MkDocs

For full documentation visit [mkdocs-ng.org](https://mkdocs-ng.org/).

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    AGENTS.md     # Instructions for coding agents.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

## For AI tools

Next to each page, the build writes a Markdown copy of it, and an `llms.txt`
that lists them all, so chat assistants and coding agents can read your
documentation. `AGENTS.md` tells coding agents how to work on this project.
"""

agents_text = """# AGENTS.md

This project is a documentation site built with
[MkDocs NG](https://mkdocs-ng.org/).

## Commands

- `mkdocs serve`: preview the site at http://127.0.0.1:8000/, rebuilt on every change.
- `mkdocs build --strict`: build the site into `site/`. It fails on broken
  links and other warnings; run it before you finish a change.

## Layout

- `mkdocs.yml`: the configuration. Its options are described by the JSON
  Schema at https://mkdocs-ng.org/schema.json.
- `docs/`: the pages, one Markdown file each. `docs/index.md` is the home page.
- `site/`: the build output. Don't edit or commit it.

## Writing pages

- Write plain Markdown and start each page with one `# Title`.
- Link to other pages by their relative `.md` path, such as `[Install](install.md)`,
  not by the URL of the built page.
- Write notes and warnings as GitHub alerts: `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`.
- Keep images under `docs/`, next to the pages that use them, and give them alt text.
- If `mkdocs.yml` has a `nav`, add new pages to it. Without one, pages are
  listed in the order of their file names.
"""

log = logging.getLogger(__name__)


def _write(path: str, text: str) -> None:
    log.info(f"Writing {os.path.basename(path)}: {path}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def new(output_dir: str, theme: str | None = None) -> None:
    """
    Create a new project in `output_dir`.

    Without `theme`, the project uses Sumi when it is installed and the
    built-in `mkdocs` theme otherwise.
    """
    docs_dir = os.path.join(output_dir, "docs")
    config_path = os.path.join(output_dir, "mkdocs.yml")
    agents_path = os.path.join(output_dir, "AGENTS.md")
    index_path = os.path.join(docs_dir, "index.md")

    if os.path.exists(config_path):
        log.info("Project already exists.")
        return

    installed = utils.get_theme_names()
    chosen = theme
    if chosen is None:
        chosen = DEFAULT_THEME if DEFAULT_THEME in installed else "mkdocs"

    if not os.path.exists(output_dir):
        log.info(f"Creating project directory: {output_dir}")
        os.mkdir(output_dir)

    _write(config_path, config_text(chosen))

    if not os.path.exists(agents_path):
        _write(agents_path, agents_text)

    if not os.path.exists(index_path):
        if not os.path.exists(docs_dir):
            os.mkdir(docs_dir)
        _write(index_path, index_text)

    if theme is None and chosen != DEFAULT_THEME:
        log.info(
            "The project uses the built-in 'mkdocs' theme. For the modern Sumi "
            "theme, run `pip install mkdocs-sumi` and create the project again, "
            "or pick another theme with `mkdocs new --theme`."
        )
    elif chosen not in installed:
        package = THEME_PACKAGES.get(chosen)
        install = (
            f"`pip install {package}`" if package else "the package that provides it"
        )
        log.warning(
            f"The '{chosen}' theme is not installed. Install it with {install} "
            "before you build the site."
        )

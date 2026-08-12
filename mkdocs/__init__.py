#!/usr/bin/env python

from __future__ import annotations

from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mkdocs.config.defaults import MkDocsConfig

# For acceptable version formats, see https://www.python.org/dev/peps/pep-0440/
__version__ = "1.8.0"


def build(
    config_file: str | Path | IO | None = None,
    site_dir: str | Path | None = None,
    *,
    dirty: bool = False,
    strict: bool | None = None,
    theme: str | None = None,
    use_directory_urls: bool | None = None,
    **kwargs: Any,
) -> MkDocsConfig:
    """
    Build a documentation site.

    This is the programmatic equivalent of the `mkdocs build` command. The
    configuration is loaded from `config_file` (or the default `mkdocs.yml`),
    then any options passed as keyword arguments override the values from the
    file.

    Args:
        config_file: Path to the configuration file, a file-like object, or
            `None` to use `mkdocs.yml` in the current directory. Pass `-` to
            read the configuration from stdin.
        site_dir: Directory to output the built site to. Overrides the
            `site_dir` value from the config file.
        dirty: Only rebuild pages that have changed, instead of doing a full
            clean build. Equivalent to `mkdocs build --dirty`.
        strict: Enable strict mode, which aborts the build on any warnings.
            Overrides the `strict` value from the config file.
        theme: The theme to use when building the documentation. Overrides
            the `theme` value from the config file.
        use_directory_urls: Use directory URLs when building pages.
            Overrides the `use_directory_urls` value from the config file.
        **kwargs: Any other configuration option to override the values from
            the config file, for example `site_name`, `nav` or `plugins`.

    Returns:
        The loaded configuration, with all defaults and overrides applied.
        For example, the built site can be found at `config.site_dir`.

    Example:
        ```python
        import mkdocs

        config = mkdocs.build(
            config_file="mkdocs.yml",
            site_name="My project",
        )
        print(f"Built site to {config.site_dir}")
        ```
    """
    from mkdocs.commands.build import build as _build
    from mkdocs.config import load_config

    if isinstance(config_file, Path):
        config_file = str(config_file)
    if isinstance(site_dir, Path):
        site_dir = str(site_dir)

    config = load_config(
        config_file=config_file,
        site_dir=site_dir,
        strict=strict,
        theme=theme,
        use_directory_urls=use_directory_urls,
        **kwargs,
    )
    config.plugins.on_startup(command="build", dirty=dirty)
    try:
        _build(config, dirty=dirty)
    finally:
        config.plugins.on_shutdown()
    return config


def serve(
    config_file: str | Path | IO | None = None,
    *,
    dev_addr: str | None = None,
    livereload: bool = True,
    build_type: str | None = None,
    watch_theme: bool = False,
    watch: Sequence[str] = (),
    open_in_browser: bool = False,
    strict: bool | None = None,
    theme: str | None = None,
    use_directory_urls: bool | None = None,
    **kwargs: Any,
) -> None:
    """
    Run the built-in development server.

    This is the programmatic equivalent of the `mkdocs serve` command. It
    blocks until the server is shut down (for example with Ctrl+C or SIGTERM).

    Args:
        config_file: Path to the configuration file, a file-like object, or
            `None` to use `mkdocs.yml` in the current directory.
        dev_addr: IP address and port to serve the documentation on, for
            example `"127.0.0.1:8000"`. Defaults to `"localhost:8000"`.
        livereload: Enable live reloading, which rebuilds the documentation
            and refreshes the browser when files change. Defaults to `True`.
        build_type: `"dirty"` to only rebuild files that have changed,
            `"clean"` to do a full clean build, or `None` for the default
            behavior. Equivalent to the `--dirty` and `--clean` options.
        watch_theme: Include the theme in the files watched for live
            reloading. Ignored when `livereload` is disabled.
        watch: Additional directories or files to watch for live reloading.
            Ignored when `livereload` is disabled.
        open_in_browser: Open the site in a web browser after the initial
            build finishes.
        strict: Enable strict mode, which aborts the build on any warnings.
            Overrides the `strict` value from the config file.
        theme: The theme to use when building the documentation. Overrides
            the `theme` value from the config file.
        use_directory_urls: Use directory URLs when building pages.
            Overrides the `use_directory_urls` value from the config file.
        **kwargs: Any other configuration option to override the values from
            the config file, for example `site_name`, `nav` or `plugins`.
    """
    from mkdocs.commands.serve import serve as _serve

    if isinstance(config_file, Path):
        config_file = str(config_file)

    _serve(
        config_file=config_file,
        dev_addr=dev_addr,
        livereload=livereload,
        build_type=build_type,
        watch_theme=watch_theme,
        watch=list(watch),
        open_in_browser=open_in_browser,
        strict=strict,
        theme=theme,
        use_directory_urls=use_directory_urls,
        **kwargs,
    )

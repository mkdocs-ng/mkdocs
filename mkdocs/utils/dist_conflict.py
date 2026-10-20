"""
Detect the upstream `mkdocs` distribution installed next to `mkdocs-ng`.

Both distributions install the same `mkdocs/` package. Most plugins and themes
depend on the `mkdocs` distribution name, so installing one of them pulls the
upstream package in, and it silently overwrites (part of) MkDocs NG. Running
`pip uninstall mkdocs` afterwards then deletes MkDocs NG's files as well.
"""

from __future__ import annotations

import functools
import logging
from importlib import metadata
from pathlib import Path

import mkdocs

log = logging.getLogger(__name__)

UPSTREAM_DIST = "mkdocs"
DOCS_URL = "https://mkdocs-ng.github.io/mkdocs/user-guide/installation/#installing-plugins-and-themes"


def find_conflicting_distribution() -> metadata.Distribution | None:
    """
    Return the upstream `mkdocs` distribution if it shares our install location.

    An upstream package installed somewhere else (for example in another
    environment that happens to be on `sys.path`) doesn't overwrite anything,
    so it isn't reported.
    """
    try:
        dist = metadata.distribution(UPSTREAM_DIST)
    except metadata.PackageNotFoundError:
        return None
    if (dist.metadata["Name"] or "").lower() != UPSTREAM_DIST:
        return None
    try:
        upstream_init = Path(str(dist.locate_file("mkdocs/__init__.py"))).resolve()
        our_init = Path(mkdocs.__file__).resolve()
    except (OSError, TypeError):  # pragma: no cover - defensive
        return dist
    if upstream_init != our_init:
        return None
    return dist


def _fix_command(dist: metadata.Distribution) -> str:
    installer = (dist.read_text("INSTALLER") or "").strip().lower()
    if installer == "uv":
        return (
            "uv pip uninstall mkdocs && uv pip install --reinstall --no-deps mkdocs-ng"
        )
    return (
        "pip uninstall -y mkdocs && pip install --force-reinstall --no-deps mkdocs-ng"
    )


@functools.cache
def warn_if_upstream_installed() -> bool:
    """
    Log a warning if the upstream `mkdocs` distribution is installed too.

    Only checks once per process. This runs before the build starts, so the
    warning is never counted by `strict` mode. Returns True if the upstream
    distribution was found.
    """
    dist = find_conflicting_distribution()
    if dist is None:
        return False

    log.warning(
        f"The upstream 'mkdocs' package (version {dist.version}) is installed in the "
        f"same environment as 'mkdocs-ng'. Both install the same 'mkdocs/' files, so "
        f"MkDocs NG may have been partly overwritten, and 'pip uninstall mkdocs' would "
        f"remove MkDocs NG too. It's usually pulled in by a plugin or theme that "
        f"depends on 'mkdocs'. To repair this environment, run:\n\n"
        f"    {_fix_command(dist)}\n\n"
        f"To keep it from coming back, see {DOCS_URL}"
    )
    return True

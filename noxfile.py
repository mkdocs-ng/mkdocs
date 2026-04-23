"""
Nox sessions for MkDocs NG development tasks.

Usage:
    nox -l                    # list all sessions
    nox -s lint               # run one session
    nox -s tests coverage     # run multiple sessions
    nox                       # run default sessions (tests + lint + typing)
"""

from __future__ import annotations

import ast
from pathlib import Path
import re

import nox

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Python version used for sessions that don't need a specific version.
DEFAULT_PYTHON = "3.11"

# All Python runtimes we support in CI.
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "pypy3"]

# Source directories checked by formatters / type-checkers.
SOURCE_DIRS = ["mkdocs", "docs"]

# Sessions that run by default when `nox` is invoked with no arguments.
nox.options.sessions = ["tests", "lint", "typing"]


def install_min_versions(session: nox.Session) -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^min-versions = (\[.*?^])", pyproject)
    if match is None:
        raise RuntimeError("Failed to load min-versions from pyproject.toml")
    dependencies = [dep.replace(" == ", "==") for dep in ast.literal_eval(match.group(1))]
    session.run("python", "-m", "pip", "install", "--force-reinstall", *dependencies)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the unit test suite."""
    session.install("-e", ".[i18n,testing]")
    session.run(
        "python",
        "-m",
        "unittest",
        "discover",
        "-s",
        "mkdocs",
        "-p",
        "*tests.py",
    )


@nox.session(name="tests-min", python=PYTHON_VERSIONS)
def tests_min(session: nox.Session) -> None:
    """Run the unit test suite with pinned minimum dependency versions."""
    session.install("-e", ".[i18n,testing]")
    install_min_versions(session)
    session.run(
        "python",
        "-m",
        "unittest",
        "discover",
        "-s",
        "mkdocs",
        "-p",
        "*tests.py",
    )


@nox.session(python=PYTHON_VERSIONS)
def coverage(session: nox.Session) -> None:
    """Run unit tests and produce a coverage report."""
    session.install("-e", ".[i18n,testing]")
    session.run(
        "coverage",
        "run",
        "--source=mkdocs",
        "--omit",
        "mkdocs/tests/*",
        "-m",
        "unittest",
        "discover",
        "-s",
        "mkdocs",
        "-p",
        "*tests.py",
    )
    session.run("coverage", "xml")
    session.run("coverage", "report", "--show-missing")


@nox.session(python=PYTHON_VERSIONS)
def integration(session: nox.Session) -> None:
    """Run the integration test suite (with babel / i18n support)."""
    session.install("-e", ".[i18n,docs]")
    session.run("python", "-m", "mkdocs.tests.integration")


@nox.session(name="integration-no-babel", python=PYTHON_VERSIONS)
def integration_no_babel(session: nox.Session) -> None:
    """Run the integration test suite without babel."""
    session.install("-e", ".[docs]")
    session.run("python", "-m", "mkdocs.tests.integration")


# ---------------------------------------------------------------------------
# Lint & formatting
# ---------------------------------------------------------------------------


@nox.session(python=DEFAULT_PYTHON)
def lint(session: nox.Session) -> None:
    """Lint Python source with Ruff."""
    session.install(".[style]")
    session.run("ruff", "check", *SOURCE_DIRS, *session.posargs)


@nox.session(name="format-check", python=DEFAULT_PYTHON)
def format_check(session: nox.Session) -> None:
    """Check code formatting with isort, Black and Ruff (no changes made — CI-safe)."""
    session.install(".[style]")
    session.run("isort", "--check-only", "--diff", *SOURCE_DIRS)
    session.run("black", "-q", "--check", "--diff", *SOURCE_DIRS)
    session.run("ruff", "check", *SOURCE_DIRS)


@nox.session(python=DEFAULT_PYTHON)
def format(session: nox.Session) -> None:
    """Auto-fix code style: isort + Black + Ruff --fix."""
    session.install(".[style]")
    session.run("ruff", "check", "--fix", *SOURCE_DIRS)
    session.run("isort", "-q", *SOURCE_DIRS)
    session.run("black", "-q", *SOURCE_DIRS)


# ---------------------------------------------------------------------------
# Type checking
# ---------------------------------------------------------------------------


@nox.session(python=DEFAULT_PYTHON)
def typing(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.install("-e", ".[i18n,typing]")
    session.run("mypy", "mkdocs")


# ---------------------------------------------------------------------------
# Other linters (Node-based, run without a virtualenv)
# ---------------------------------------------------------------------------


@nox.session(venv_backend="none")
def markdown(session: nox.Session) -> None:
    """Lint Markdown files with markdownlint-cli (requires Node / npx)."""
    session.run(
        "npm",
        "exec",
        "--yes",
        "--",
        "markdownlint-cli",
        "README.md",
        "CONTRIBUTING.md",
        "docs/",
        "--ignore",
        "docs/CNAME",
        external=True,
    )


@nox.session(venv_backend="none")
def js(session: nox.Session) -> None:
    """Lint JavaScript files with jshint (requires Node / npx)."""
    session.run(
        "npm",
        "exec",
        "--yes",
        "--",
        "jshint",
        "mkdocs/",
        external=True,
    )


@nox.session(python=DEFAULT_PYTHON)
def spelling(session: nox.Session) -> None:
    """Check spelling with codespell."""
    session.install(".[spelling]")
    session.run(
        "codespell",
        "mkdocs",
        "docs",
        "*.*",
        "-S",
        "LC_MESSAGES",
        "-S",
        "*.min.js",
        "-S",
        "lunr*.js",
        "-S",
        "fontawesome-webfont.svg",
        "-S",
        "tinyseg.js",
        "-S",
        "*.map",
    )


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------


@nox.session(python=DEFAULT_PYTHON)
def docs(session: nox.Session) -> None:
    """Build the documentation site."""
    session.install("-e", ".[i18n,docs]")
    session.run("mkdocs", "build")


@nox.session(name="docs-serve", python=DEFAULT_PYTHON)
def docs_serve(session: nox.Session) -> None:
    """Serve the documentation site locally with live-reload."""
    session.install("-e", ".[i18n,docs]")
    session.run("mkdocs", "serve")


@nox.session(name="docs-deploy", python=DEFAULT_PYTHON)
def docs_deploy(session: nox.Session) -> None:
    """Deploy the documentation site to GitHub Pages (gh-pages branch)."""
    session.install("-e", ".[i18n,docs]")
    session.run("mkdocs", "gh-deploy", "--force")

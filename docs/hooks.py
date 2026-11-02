from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.version import Version

try:
    from click._utils import UNSET as CLICK_UNSET
except ImportError:  # click < 8.3
    CLICK_UNSET = None

if TYPE_CHECKING:
    import click

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.nav import Page

LEGACY_REPO_URL = "https://github.com/mkdocs/mkdocs"
CURRENT_REPO_URL = "https://github.com/mkdocs-ng/mkdocs"
RELEASE_NOTES_CUTOFF = Version("1.7.0")
RELEASE_NOTES_SECTION_RE = re.compile(
    r"^## Version (?P<version>\S+) \([^)]+\)\s*$", re.MULTILINE
)
FENCED_CODE_BLOCK_RE = re.compile(r"(^```.*?^```[ \t]*$)", re.MULTILINE | re.DOTALL)
ISSUE_REF_RE = re.compile(r"(?<![\w/`\[])#(?P<number>\d+)\b")
VERSION_EXAMPLE_RE = re.compile(r"mkdocs, version \S+ from")


def _get_language_of_translation_file(path: Path) -> str:
    with path.open(encoding="utf-8") as f:
        translation_line = f.readline()
    m = re.search("^# (.+) translations ", translation_line)
    assert m
    return m[1]


def _repo_url_for_release(version: str) -> str:
    if Version(version) >= RELEASE_NOTES_CUTOFF:
        return CURRENT_REPO_URL
    return LEGACY_REPO_URL


def _rewrite_issue_refs(text: str, repo_url: str) -> str:
    def replacement(m: re.Match[str]) -> str:
        number = m["number"]
        return f"[#{number}]({repo_url}/issues/{number})"

    return ISSUE_REF_RE.sub(replacement, text)


def _rewrite_release_notes_section(text: str, repo_url: str) -> str:
    def rewrite_chunk(chunk: str) -> str:
        chunk = chunk.replace(LEGACY_REPO_URL, repo_url)
        chunk = chunk.replace(CURRENT_REPO_URL, repo_url)
        return _rewrite_issue_refs(chunk, repo_url)

    parts = FENCED_CODE_BLOCK_RE.split(text)
    return "".join(
        part if i % 2 else rewrite_chunk(part) for i, part in enumerate(parts)
    )


def _rewrite_release_notes_links(markdown: str) -> str:
    matches = list(RELEASE_NOTES_SECTION_RE.finditer(markdown))
    if not matches:
        return markdown

    result = []
    cursor = 0
    for i, match in enumerate(matches):
        result.append(markdown[cursor : match.start()])
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        section = markdown[match.start() : end]
        result.append(
            _rewrite_release_notes_section(
                section, _repo_url_for_release(match["version"])
            )
        )
        cursor = end
    return "".join(result)


def _update_version_example(markdown: str) -> str:
    """Keep the `mkdocs --version` sample output in sync with the current release."""
    import mkdocs

    return VERSION_EXAMPLE_RE.sub(
        f"mkdocs, version {mkdocs.__version__} from", markdown, count=1
    )


def _documented_default(option: click.Option) -> object:
    """
    The default to show for a CLI option, as click before 8.3 reported it.

    Since click 8.3, an option without a default has `click._utils.UNSET` as its
    default, and mkdocs-click (0.9.0, the latest) prints it as `Sentinel.UNSET`.
    """
    if CLICK_UNSET is None or option.default is not CLICK_UNSET:
        return option.default
    return False if option.is_bool_flag else None


def _fix_cli_page_defaults() -> None:
    """Make mkdocs-click show `False` or `None` instead of `Sentinel.UNSET`."""
    try:
        from mkdocs_click import _docs
    except ImportError:  # pragma: no cover
        return
    original = _docs._format_table_option_row
    if getattr(original, "_shows_documented_default", False):
        return

    def format_row(option: click.Option) -> str:
        default = _documented_default(option)
        if default is not option.default:
            option = copy.copy(option)
            option.default = default
        return original(option)

    format_row._shows_documented_default = True  # type: ignore[attr-defined]
    _docs._format_table_option_row = format_row


def on_config(config: MkDocsConfig) -> None:
    _fix_cli_page_defaults()


def on_page_markdown(
    markdown: str, page: Page, config: MkDocsConfig, **kwargs
) -> str | None:
    if page.file.src_uri == "about/release-notes.md":
        return _rewrite_release_notes_links(_update_version_example(markdown))

    if page.file.src_uri == "user-guide/choosing-your-theme.md":
        here = Path(config.config_file_path).parent

        def replacement(m: re.Match) -> str:
            lines = []
            for d in sorted(here.glob(m[2])):
                lang = _get_language_of_translation_file(
                    Path(d, "LC_MESSAGES", "messages.po")
                )
                lines.append(f"{m[1]}`{d.name}`: {lang}")
            return "\n".join(lines)

        return re.sub(
            r"^( *\* )\(see the list of existing directories `(.+)`\)$",
            replacement,
            markdown,
            flags=re.MULTILINE,
        )

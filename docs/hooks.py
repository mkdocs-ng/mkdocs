from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.version import Version

if TYPE_CHECKING:
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


def on_page_markdown(
    markdown: str, page: Page, config: MkDocsConfig, **kwargs
) -> str | None:
    if page.file.src_uri == "about/release-notes.md":
        return _rewrite_release_notes_links(markdown)

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

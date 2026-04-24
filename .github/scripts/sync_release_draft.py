from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RELEASE_NOTES_PATH = Path("docs/about/release-notes.md")
CANONICAL_URL = "https://mkdocs-ng.github.io/mkdocs/about/release-notes/"
VERSION_RE = re.compile(
    r"^## Version (?P<version>\S+) \((?P<date>[^)]+)\)\s*$", re.MULTILINE
)


def extract_latest_release_section(text: str) -> tuple[str, str]:
    matches = list(VERSION_RE.finditer(text))
    if not matches:
        raise SystemExit(f"No release section found in {RELEASE_NOTES_PATH}")

    current = matches[0]
    end = matches[1].start() if len(matches) > 1 else len(text)
    version = current.group("version")
    section = text[current.start() : end].strip()
    section = re.sub(r"\n+---\s*$", "", section)
    return version, section


def release_tag_for_version(version: str) -> str:
    return version if version.startswith("v") else f"v{version}"


def release_name_for_version(version: str) -> str:
    return release_tag_for_version(version)


def write_github_output(version: str, body: str) -> None:
    release_tag = release_tag_for_version(version)
    release_name = release_name_for_version(version)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        sys.stdout.write(f"{version}\n{release_tag}\n{release_name}\n\n{body}\n")
        return

    body_path = Path(os.environ.get("RUNNER_TEMP", ".")) / "release-draft-body.md"
    body_path.write_text(body, encoding="utf-8")

    with Path(github_output).open("a", encoding="utf-8") as fh:
        print(f"version={version}", file=fh)
        print(f"release_tag={release_tag}", file=fh)
        print(f"release_name={release_name}", file=fh)
        print(f"body_path={body_path}", file=fh)


def main() -> None:
    text = RELEASE_NOTES_PATH.read_text(encoding="utf-8")
    version, section = extract_latest_release_section(text)
    body = f"{section}\n\n---\nCanonical release notes: {CANONICAL_URL}"
    write_github_output(version, body)


if __name__ == "__main__":
    main()

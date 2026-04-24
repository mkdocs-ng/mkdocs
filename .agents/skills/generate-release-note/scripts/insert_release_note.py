#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_RELEASE_NOTES = Path("docs/about/release-notes.md")
VERSION_HEADING_RE = re.compile(r"^## Version .+ \([^)]+\)\s*$", re.MULTILINE)
CATEGORY_HEADING_RE = re.compile(r"^### (?P<category>.+?)\s*$", re.MULTILINE)


def normalize_note(note: str) -> str:
    note = note.strip()
    if not note:
        raise SystemExit("Release note cannot be empty.")
    if not note.startswith("* "):
        note = f"* {note}"
    return note


def find_latest_release_section(text: str) -> tuple[int, int]:
    matches = list(VERSION_HEADING_RE.finditer(text))
    if not matches:
        raise SystemExit("No '## Version ... (...)' release section found.")

    start = matches[0].start()
    end = matches[1].start() if len(matches) > 1 else len(text)
    return start, end


def find_category(section: str, category: str) -> tuple[int, int] | None:
    matches = list(CATEGORY_HEADING_RE.finditer(section))
    for index, match in enumerate(matches):
        if match.group("category").strip().casefold() == category.casefold():
            start = match.end()
            end = (
                matches[index + 1].start() if index + 1 < len(matches) else len(section)
            )
            return start, end
    return None


def append_to_category(section: str, category: str, note: str) -> str:
    existing = find_category(section, category)
    if existing is None:
        section = section.rstrip()
        return f"{section}\n\n### {category}\n\n{note}\n\n"

    _category_start, category_end = existing
    before = section[:category_end].rstrip()
    after = section[category_end:].lstrip("\n")

    if note in before:
        return section

    inserted = f"{before}\n{note}\n"
    if after:
        return f"{inserted}\n{after}"
    return inserted


def insert_release_note(text: str, category: str, note: str) -> str:
    section_start, section_end = find_latest_release_section(text)
    section = text[section_start:section_end]
    new_section = append_to_category(section, category, note)
    return f"{text[:section_start]}{new_section}{text[section_end:]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert a release note bullet into the latest release section."
    )
    parser.add_argument("--note", required=True, help="Release note bullet to insert.")
    parser.add_argument(
        "--category",
        required=True,
        help="Target category heading, for example Fixed, Added, Changed, or Maintenance.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_RELEASE_NOTES,
        help=f"Release notes file to update. Defaults to {DEFAULT_RELEASE_NOTES}.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the updated file content without writing it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    note = normalize_note(args.note)
    text = args.file.read_text(encoding="utf-8")
    updated = insert_release_note(text, args.category.strip(), note)

    if args.dry_run:
        sys.stdout.write(updated)
        return

    if updated != text:
        args.file.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()

"""
Deterministic documentation corpus used by the benchmarks.

Everything here is generated from a fixed pseudo-random seed so that every
benchmark run measures exactly the same workload and results only move when
MkDocs itself changes.
"""

from __future__ import annotations

import os
import random

WORDS = (
    "documentation markdown static site generator theme plugin navigation "
    "configuration template rendering directory anchor heading section link "
    "reference build server extension content page index deploy source output"
).split()

LANGUAGES = ("python", "yaml", "bash", "text")

SECTIONS = 5
PAGES_PER_SECTION = 6

MKDOCS_YML = """\
site_name: Benchmark Site
site_url: https://example.com/benchmark/
site_description: A generated site used to benchmark MkDocs.
repo_url: https://github.com/mkdocs-ng/mkdocs/
edit_uri: blob/main/docs/

theme:
  name: mkdocs

markdown_extensions:
  - toc:
      permalink: true
  - admonition
  - attr_list
  - def_list
  - footnotes
  - tables

plugins:
  - search
"""


def _sentence(rng: random.Random) -> str:
    return " ".join(rng.choices(WORDS, k=rng.randint(6, 14))).capitalize() + "."


def _paragraph(rng: random.Random) -> str:
    return " ".join(_sentence(rng) for _ in range(rng.randint(3, 6)))


def _code_block(rng: random.Random) -> str:
    lines = "\n".join(
        f"    {rng.choice(WORDS)} = {rng.randint(0, 1000)}"
        for _ in range(rng.randint(3, 8))
    )
    return f"```{rng.choice(LANGUAGES)}\n{lines}\n```"


def _table(rng: random.Random) -> str:
    header = "| Option | Type | Default |\n| --- | --- | --- |"
    rows = "\n".join(
        f"| `{rng.choice(WORDS)}` | {rng.choice(WORDS)} | `{rng.randint(0, 99)}` |"
        for _ in range(rng.randint(3, 6))
    )
    return f"{header}\n{rows}"


def _bullet_list(rng: random.Random) -> str:
    return "\n".join(f"- {_sentence(rng)}" for _ in range(rng.randint(3, 6)))


def _admonition(rng: random.Random) -> str:
    return f'!!! note "{rng.choice(WORDS).title()}"\n\n    {_sentence(rng)}'


_BUILDERS = (_paragraph, _code_block, _table, _bullet_list, _admonition)


def make_markdown(seed: int, *, headings: int = 8, links: tuple[str, ...] = ()) -> str:
    """Generate a deterministic Markdown document with realistic constructs."""
    rng = random.Random(seed)
    parts = [
        "---",
        f"title: Page {seed}",
        "tags:",
        f"  - {rng.choice(WORDS)}",
        f"  - {rng.choice(WORDS)}",
        "---",
        "",
        f"# Page {seed} about {rng.choice(WORDS)}",
        "",
        _paragraph(rng),
    ]
    for i in range(headings):
        level = "##" if i % 3 else "###"
        parts += ["", f"{level} {rng.choice(WORDS).title()} {i}", "", _paragraph(rng)]
        parts += ["", _BUILDERS[i % len(_BUILDERS)](rng)]
        if links:
            target = links[i % len(links)]
            parts += [
                "",
                f"See [{rng.choice(WORDS)}]({target}) and "
                f"[{rng.choice(WORDS)}]({target}#{rng.choice(WORDS)}) for details.",
            ]
    return "\n".join(parts) + "\n"


def write_site(root: str) -> str:
    """
    Write a full MkDocs project (config + nested docs tree) under `root`.

    Returns the path of the generated `mkdocs.yml`.
    """
    docs_dir = os.path.join(root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    section_names = [f"section-{i:02d}" for i in range(SECTIONS)]

    with open(os.path.join(docs_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write(make_markdown(0, links=tuple(f"{n}/index.md" for n in section_names)))

    for s, name in enumerate(section_names):
        section_dir = os.path.join(docs_dir, name)
        os.makedirs(section_dir, exist_ok=True)
        page_names = tuple(f"page-{p:02d}.md" for p in range(PAGES_PER_SECTION))
        links = ("../index.md", *page_names)
        with open(os.path.join(section_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(make_markdown(100 + s, links=links))
        for p, page_name in enumerate(page_names):
            with open(os.path.join(section_dir, page_name), "w", encoding="utf-8") as f:
                f.write(make_markdown(1000 + s * 100 + p, links=links))

    # A few static assets, so the file collection is not only Markdown.
    css_dir = os.path.join(docs_dir, "css")
    os.makedirs(css_dir, exist_ok=True)
    for i in range(3):
        with open(os.path.join(css_dir, f"extra-{i}.css"), "w", encoding="utf-8") as f:
            f.write("body { margin: 0; }\n")

    config_file = os.path.join(root, "mkdocs.yml")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(MKDOCS_YML)
    return config_file

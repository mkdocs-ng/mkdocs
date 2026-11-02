r"""
Compare the build speed of MkDocs NG with other documentation tools.

This is the script behind the numbers on the "Comparison" page of the docs.
Every tool gets the same Markdown, from `benchmarks/corpus.py`, and runs on the
same machine one after the other. Install each tool in its own environment
first (see `benchmarks/README.md`), then:

    python -m benchmarks.compare corpus /tmp/bench/1000 --pages 1000
    python -m benchmarks.compare build /tmp/bench/1000 \
        --tool "ng=/venvs/ng/bin/mkdocs build -q -f mkdocs-mkdocs.yml -d {out}" \
        --tool "mkdocs=/venvs/up/bin/mkdocs build -q -f mkdocs-mkdocs.yml -d {out}"
    python -m benchmarks.compare build /tmp/bench/1000 --before "rm -rf site .cache" \
        --tool "zensical=/venvs/zs/bin/zensical build -f zensical.yml"
    python -m benchmarks.compare serve /tmp/bench/1000 \
        --tool "ng=/venvs/ng/bin/mkdocs serve -f mkdocs-mkdocs.yml -a 127.0.0.1:{port}"

`corpus` writes the site, MkDocs configs for several themes (`mkdocs-mkdocs.yml`,
`mkdocs-material.yml`, `mkdocs-sumi.yml`), a `zensical.yml`, and the same pages
as Sphinx, VitePress, Docusaurus and Starlight projects under `other/`.

`build` times clean builds: `{out}` is an empty output directory for each run.
`--before` runs an untimed command before each run, to remove a tool's cache
or the output of a tool that builds into its own directory. `serve` starts
each server, edits one page and times how long the server takes to return the
new text.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request

from benchmarks.corpus import write_site

# The page that `serve` edits, and its URL path.
EDITED_PAGE = "docs/section-03/page-07.md"
EDITED_URL = "section-03/page-07/"


def _sections(pages: int) -> tuple[int, int]:
    """Split `pages` into sections of about 50 pages, like a large real site."""
    sections = max(1, round(pages / 50))
    per_section = max(1, round((pages - 1) / sections) - 1)
    return sections, per_section


def write_corpus(root: str, pages: int) -> None:
    shutil.rmtree(root, ignore_errors=True)
    sections, per_section = _sections(pages)
    config_file = write_site(root, sections=sections, pages_per_section=per_section)
    docs_dir = os.path.join(root, "docs")
    # The corpus links to random anchors that don't exist. Zensical reports each
    # one, which slows it down, so link to the pages only.
    for dirpath, _, filenames in os.walk(docs_dir):
        for name in filenames:
            if name.endswith(".md"):
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                text = _strip_anchors(text)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)

    with open(config_file, encoding="utf-8") as f:
        base = f.read()
    _write(root, "mkdocs-mkdocs.yml", base)
    _write(
        root, "mkdocs-material.yml", base.replace("name: mkdocs\n", "name: material\n")
    )
    _write(
        root,
        "mkdocs-sumi.yml",
        base.replace("name: mkdocs\n", "name: sumi\n").replace(
            "  - search\n", "  - search\n  - sumi\n"
        ),
    )
    # Zensical reads mkdocs.yml, has its own theme and search.
    _write(
        root,
        "zensical.yml",
        base.replace("name: mkdocs\n", "name: material\n").split("plugins:")[0],
    )
    _write_other(root, docs_dir)
    count = sum(
        name.endswith(".md") for _, _, names in os.walk(docs_dir) for name in names
    )
    _say(f"{root}: {count} pages")


def _strip_anchors(text: str) -> str:
    import re

    return re.sub(r"\.md#[a-z]+\)", ".md)", text)


def _write(root: str, name: str, content: str) -> None:
    path = os.path.join(root, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _copy_docs(docs_dir: str, dest: str, fix=lambda text: text) -> None:
    for dirpath, _, filenames in os.walk(docs_dir):
        for name in filenames:
            if not name.endswith(".md"):
                continue
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, docs_dir)
            with open(src, encoding="utf-8") as f:
                _write(dest, rel, fix(f.read()))


def _write_other(root: str, docs_dir: str) -> None:
    """The same pages as Sphinx, VitePress, Docusaurus and Starlight projects."""
    sections = sorted(d for d in os.listdir(docs_dir) if d.startswith("section-"))

    def pages(section: str) -> list[str]:
        names = os.listdir(os.path.join(docs_dir, section))
        return sorted(n[:-3] for n in names if n.endswith(".md") and n != "index.md")

    other = os.path.join(root, "other")

    # Sphinx with MyST: every section is a toctree.
    sphinx = os.path.join(other, "sphinx", "docs")
    _copy_docs(docs_dir, sphinx)
    _write(
        sphinx,
        "conf.py",
        'project = "Benchmark Site"\n'
        'extensions = ["myst_parser"]\n'
        'html_theme = "alabaster"\n'
        'source_suffix = {".md": "markdown"}\n'
        'myst_enable_extensions = ["deflist", "attrs_inline"]\n'
        'suppress_warnings = ["myst.xref_missing", "myst.header", "misc.highlighting_failure"]\n',
    )

    def toctree(entries: list[str]) -> str:
        return "\n```{toctree}\n:hidden:\n" + "\n".join(entries) + "\n```\n"

    with open(os.path.join(sphinx, "index.md"), "a", encoding="utf-8") as f:
        f.write(toctree([f"{s}/index" for s in sections]))
    for s in sections:
        with open(os.path.join(sphinx, s, "index.md"), "a", encoding="utf-8") as f:
            f.write(toctree(pages(s)))

    # VitePress: Markdown goes through Vue, so `{` needs escaping.
    vitepress = os.path.join(other, "vitepress")
    _copy_docs(
        docs_dir, os.path.join(vitepress, "docs"), lambda t: t.replace("{", "&#123;")
    )
    sidebar = [
        {
            "text": s,
            "link": f"/{s}/",
            "items": [{"text": p, "link": f"/{s}/{p}"} for p in pages(s)],
        }
        for s in sections
    ]
    config = {
        "title": "Benchmark Site",
        "themeConfig": {"sidebar": sidebar, "search": {"provider": "local"}},
    }
    _write(
        vitepress,
        "docs/.vitepress/config.mjs",
        f"export default {json.dumps(config)}\n",
    )
    _write(vitepress, "package.json", '{"type": "module", "private": true}\n')

    # Docusaurus, reading the pages as plain Markdown (not MDX).
    docusaurus = os.path.join(other, "docusaurus")
    _copy_docs(
        docs_dir,
        os.path.join(docusaurus, "docs"),
        lambda t: t.replace("{", "\\{").replace("<", "&lt;"),
    )
    _write(
        docusaurus,
        "docusaurus.config.js",
        "module.exports = {title: 'Benchmark Site', url: 'https://example.com', baseUrl: '/',\n"
        "  onBrokenLinks: 'ignore', onBrokenAnchors: 'ignore', markdown: {format: 'md'},\n"
        "  presets: [['@docusaurus/preset-classic', {docs: {routeBasePath: '/',\n"
        "    sidebarPath: require.resolve('./sidebars.js')}, blog: false}]]};\n",
    )
    _write(
        docusaurus,
        "sidebars.js",
        "module.exports = {docs: [{type: 'autogenerated', dirName: '.'}]};\n",
    )
    _write(docusaurus, "package.json", '{"private": true}\n')

    # Astro Starlight.
    starlight = os.path.join(other, "starlight")
    _copy_docs(docs_dir, os.path.join(starlight, "src", "content", "docs"))
    _write(
        starlight,
        "src/content.config.ts",
        "import { defineCollection } from 'astro:content';\n"
        "import { docsLoader } from '@astrojs/starlight/loaders';\n"
        "import { docsSchema } from '@astrojs/starlight/schema';\n"
        "export const collections = { docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }) };\n",
    )
    groups = ", ".join(
        f"{{label: '{s}', items: [{{autogenerate: {{directory: '{s}'}}}}]}}"
        for s in sections
    )
    _write(
        starlight,
        "astro.config.mjs",
        "import { defineConfig } from 'astro/config';\n"
        "import starlight from '@astrojs/starlight';\n"
        "export default defineConfig({ integrations: [starlight({ title: 'Benchmark Site',\n"
        f"  sidebar: [{groups}] }})] }});\n",
    )
    _write(starlight, "package.json", '{"type": "module", "private": true}\n')


def _say(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _parse_tools(specs: list[str]) -> list[tuple[str, str]]:
    tools = []
    for spec in specs:
        label, sep, command = spec.partition("=")
        if not sep:
            sys.exit(f"--tool must look like LABEL=COMMAND, got {spec!r}")
        tools.append((label.strip(), command.strip()))
    return tools


def _env() -> dict[str, str]:
    return dict(
        os.environ,
        DISABLE_MKDOCS_2_WARNING="true",
        NO_COLOR="1",
        ASTRO_TELEMETRY_DISABLED="1",
    )


def build(
    root: str,
    tools: list[tuple[str, str]],
    runs: int,
    cwd: str | None,
    before: str | None = None,
) -> dict:
    results = {}
    for label, command in tools:
        times = []
        for _ in range(runs):
            out = tempfile.mkdtemp(prefix="bench-out-")
            shutil.rmtree(out)
            if before:
                # Untimed, such as removing a tool's cache or last output.
                subprocess.run(before, shell=True, cwd=cwd or root, check=True)
            start = time.perf_counter()
            proc = subprocess.run(
                command.format(out=out),
                shell=True,
                cwd=cwd or root,
                env=_env(),
                capture_output=True,
                text=True,
            )
            elapsed = time.perf_counter() - start
            shutil.rmtree(out, ignore_errors=True)
            if proc.returncode:
                sys.stderr.write(f"{label}: failed\n{proc.stderr[-2000:]}\n")
                break
            times.append(elapsed)
        if times:
            results[label] = times
            _say(
                f"{label:<24} median {statistics.median(times):8.2f} s   runs: "
                + ", ".join(f"{t:.2f}" for t in times)
            )
    return results


def _get(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.read().decode("utf-8", "replace")
    except Exception:
        return ""


def serve(root: str, tools: list[tuple[str, str]], edits: int, port: int) -> dict:
    results = {}
    page = os.path.join(root, EDITED_PAGE)
    if not os.path.exists(page):
        sys.exit(f"serve edits {EDITED_PAGE}: write a site of at least 200 pages")
    with open(page, encoding="utf-8") as f:
        original = f.read()
    for index, (label, command) in enumerate(tools):
        # A new port for each tool, so that a server still shutting down
        # can't answer for the next one.
        tool_port = port + index
        proc = subprocess.Popen(
            command.format(port=tool_port),
            shell=True,
            cwd=root,
            env=_env(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            start = time.perf_counter()
            urls = [
                f"http://127.0.0.1:{tool_port}/{p}{EDITED_URL}"
                for p in ("benchmark/", "")
            ]
            url = None
            while url is None:
                if time.perf_counter() - start > 900:
                    raise TimeoutError(f"{label} didn't serve the site")
                url = next((u for u in urls if "Page 1307" in _get(u)), None)
                time.sleep(0.05)
            first = time.perf_counter() - start
            time.sleep(3)
            latencies = []
            for i in range(edits):
                marker = f"EDITED{i}x{random.randrange(10**9)}"
                with open(page, "w", encoding="utf-8") as f:
                    f.write(f"{original}\n\n{marker}\n")
                start = time.perf_counter()
                while marker not in _get(url):
                    if time.perf_counter() - start > 300:
                        raise TimeoutError(f"{label} didn't show the edit")
                    time.sleep(0.02)
                latencies.append(time.perf_counter() - start)
                time.sleep(2)
        finally:
            with open(page, "w", encoding="utf-8") as f:
                f.write(original)
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait()
        results[label] = {"first": first, "edits": latencies}
        _say(
            f"{label:<24} first page {first:6.2f} s   edit shown after median "
            f"{statistics.median(latencies):5.2f} s   runs: "
            + ", ".join(f"{t:.2f}" for t in latencies)
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("corpus", help="write the site in every format")
    p.add_argument("root")
    p.add_argument("--pages", type=int, default=1000)
    p = sub.add_parser("build", help="time clean builds")
    p.add_argument("root")
    p.add_argument(
        "--tool",
        action="append",
        required=True,
        help="LABEL=COMMAND, {out} = output dir",
    )
    p.add_argument("--runs", type=int, default=3)
    p.add_argument(
        "--cwd", help="directory to run in, relative to root (default: root)"
    )
    p.add_argument(
        "--before",
        help="untimed command to run before each run, such as clearing a cache",
    )
    p.add_argument("--json", help="also write the times to this file")
    p = sub.add_parser("serve", help="time how long an edit takes to show")
    p.add_argument("root")
    p.add_argument(
        "--tool", action="append", required=True, help="LABEL=COMMAND, {port} = port"
    )
    p.add_argument("--edits", type=int, default=5)
    p.add_argument("--port", type=int, default=8123)
    p.add_argument("--json", help="also write the times to this file")
    args = parser.parse_args()

    if args.command == "corpus":
        write_corpus(args.root, args.pages)
        return
    tools = _parse_tools(args.tool)
    if args.command == "build":
        cwd = os.path.join(args.root, args.cwd) if args.cwd else None
        results = build(args.root, tools, args.runs, cwd, args.before)
    else:
        results = serve(args.root, tools, args.edits, args.port)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()

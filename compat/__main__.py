"""
Plugin compatibility matrix.

For every case in ``cases.yaml`` this creates a fresh virtual environment per
engine, installs the plugin, builds a small site with ``mkdocs build --strict``
and records the outcome. The two engines are upstream MkDocs (the baseline) and
this checkout. A case that builds on upstream but fails here is a regression,
and makes the command exit with status 1.

Usage::

    python -m compat                        # every case, both engines
    python -m compat --only mike,mkdocs-material
    python -m compat --engine ng --jobs 8 --markdown report.md --json report.json

Requires ``uv`` on PATH; it is used to create the environments quickly.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = Path(__file__).with_name("cases.yaml")

UPSTREAM_REQUIREMENT = "mkdocs==1.6.1"
UPSTREAM_VERSION = "1.6.1"

ENGINES = ("upstream", "ng")
ENGINE_LABELS = {"upstream": f"MkDocs {UPSTREAM_VERSION}", "ng": "mkdocs-ng"}

INSTALL_TIMEOUT = 600
BUILD_TIMEOUT = 300

BASE_CONFIG = {
    "site_name": "Compat",
    "site_url": "https://example.com/compat/",
    "strict": True,
}

BASE_FILES = {
    "docs/index.md": """\
        # Home

        Welcome. Read [the guide](guide/page.md).

        ## Section

        ```python
        print("hello")
        ```
        """,
    "docs/guide/page.md": """\
        # Guide

        Back to [the section](../index.md#section).

        ## Details

        More text.
        """,
}

STATUS_ICONS = {"pass": "✅ pass", "fail": "❌ fail", "error": "⚠️ setup"}


@dataclass
class Result:
    case: str
    engine: str
    status: str  # "pass", "fail" or "error" (could not install or set up)
    seconds: float = 0.0
    version: str = ""
    log: str = ""


@dataclass
class Case:
    name: str
    rank: int
    install: list[str]
    config: dict = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)
    git: bool = False
    note: str = ""


def load_cases() -> list[Case]:
    return [
        Case(**raw) for raw in yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))
    ]


def ng_version() -> str:
    text = (ROOT / "mkdocs" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "([^"]+)"', text, re.M)
    assert match, "could not read __version__"
    return match.group(1)


def _run(cmd: list[str], cwd: Path, timeout: int, env: dict[str, str] | None = None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )


def _err(message: str) -> None:
    sys.stderr.write(message + "\n")


def _tail(text: str, lines: int = 40) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def write_site(case: Case, site: Path) -> None:
    config = {**BASE_CONFIG, **case.config}
    (site / "mkdocs.yml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    for name, content in {**BASE_FILES, **case.files}.items():
        path = site / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")


def init_git(site: Path) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Compat",
        "GIT_AUTHOR_EMAIL": "compat@example.com",
        "GIT_COMMITTER_NAME": "Compat",
        "GIT_COMMITTER_EMAIL": "compat@example.com",
    }
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "Initial commit"],
    ):
        subprocess.run(cmd, cwd=site, env=env, check=True, capture_output=True)


def install(case: Case, engine: str, work: Path, python: str) -> tuple[Path, str]:
    """Create a venv with the plugin and the engine. Return its python and a log."""
    venv = work / "venv"
    log = []
    proc = _run(
        ["uv", "venv", "-q", "--python", python, str(venv)], work, INSTALL_TIMEOUT
    )
    log.append(proc.stdout)
    if proc.returncode:
        raise RuntimeError("".join(log))
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    base = ["uv", "pip", "install", "-q", "--python", str(py)]
    engine_req = UPSTREAM_REQUIREMENT if engine == "upstream" else str(ROOT)
    steps = [[*base, *case.install, engine_req]]
    if engine == "ng":
        # Plugins depend on the upstream 'mkdocs' distribution, which ships a
        # package of the same name. Reinstall this checkout last so its files
        # are the ones that get imported.
        steps.append(
            [*base, "--reinstall-package", "mkdocs-ng", "--no-deps", str(ROOT)]
        )
    for cmd in steps:
        proc = _run(cmd, work, INSTALL_TIMEOUT)
        log.append(proc.stdout)
        if proc.returncode:
            raise RuntimeError("".join(log))

    proc = _run([str(py), "-c", "import mkdocs; print(mkdocs.__version__)"], work, 60)
    version = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    expected = UPSTREAM_VERSION if engine == "upstream" else ng_version()
    if proc.returncode or version != expected:
        raise RuntimeError(
            f"expected mkdocs {expected}, imported {version!r}\n{proc.stdout}"
        )
    return py, version


def run_case(case: Case, engine: str, python: str, keep: bool) -> Result:
    work = Path(tempfile.mkdtemp(prefix=f"mkdocs-compat-{case.name}-{engine}-"))
    try:
        try:
            py, version = install(case, engine, work, python)
            site = work / "site"
            site.mkdir()
            write_site(case, site)
            if case.git:
                init_git(site)
        except (RuntimeError, subprocess.SubprocessError, OSError) as e:
            return Result(case.name, engine, "error", log=_tail(str(e)))

        env = {
            **os.environ,
            "DISABLE_MKDOCS_2_WARNING": "true",
            "NO_MKDOCS_2_WARNING": "1",
        }
        env.pop("PYTHONPATH", None)
        start = time.perf_counter()
        try:
            proc = _run([str(py), "-m", "mkdocs", "build"], site, BUILD_TIMEOUT, env)
        except subprocess.TimeoutExpired:
            return Result(
                case.name, engine, "fail", BUILD_TIMEOUT, version, "build timed out"
            )
        seconds = time.perf_counter() - start
        status = "pass" if proc.returncode == 0 else "fail"
        return Result(
            case.name, engine, status, round(seconds, 2), version, _tail(proc.stdout)
        )
    finally:
        if keep:
            _err(f"kept {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


def verdict(results: dict[str, Result]) -> str:
    up, ng = results.get("upstream"), results.get("ng")
    if not up or not ng:
        return ""
    if ng.status == "pass":
        return "fixed" if up.status != "pass" else "ok"
    if up.status == "pass":
        return "**regression**"
    return "broken on both"


def render_markdown(
    cases: list[Case], table: dict[str, dict[str, Result]], engines
) -> str:
    head = ["Plugin", "Score", *(ENGINE_LABELS[e] for e in engines)]
    if len(engines) == 2:
        head.append("Verdict")
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    details = []
    for case in sorted(cases, key=lambda c: (-c.rank, c.name)):
        row = table.get(case.name, {})
        name = case.name + (" ¹" if case.note else "")
        cells = [name, str(case.rank)]
        for engine in engines:
            r = row.get(engine)
            cells.append(f"{STATUS_ICONS[r.status]} ({r.seconds:.1f}s)" if r else "")
            if r and r.status != "pass":
                details.append(
                    f"<details><summary>{case.name} on {ENGINE_LABELS[engine]}"
                    f" ({r.status})</summary>\n\n```text\n{r.log}\n```\n\n</details>"
                )
        if len(engines) == 2:
            cells.append(verdict(row))
        lines.append("| " + " | ".join(cells) + " |")

    passed = {e: sum(table[c.name][e].status == "pass" for c in cases) for e in engines}
    summary = ", ".join(f"{ENGINE_LABELS[e]} {passed[e]}/{len(cases)}" for e in engines)
    out = [f"## Plugin compatibility: {summary}", "", *lines]
    notes = [f"- {c.name}: {c.note}" for c in cases if c.note]
    if notes:
        out += ["", "¹ Partial check:", *notes]
    if details:
        out += ["", "### Failure logs", "", *details]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m compat", description=__doc__.split("\n\n")[1]
    )
    parser.add_argument("--only", help="comma-separated case names")
    parser.add_argument("--engine", choices=[*ENGINES, "both"], default="both")
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2))
    parser.add_argument(
        "--python", default=sys.executable, help="interpreter for the venvs"
    )
    parser.add_argument("--json", type=Path, help="write raw results here")
    parser.add_argument("--markdown", type=Path, help="write the report here")
    parser.add_argument("--keep", action="store_true", help="keep work directories")
    parser.add_argument("--list", action="store_true", help="list cases and exit")
    args = parser.parse_args(argv)

    cases = load_cases()
    if args.list:
        for case in cases:
            sys.stdout.write(f"{case.rank:>3}  {case.name}\n")
        return 0
    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        unknown = wanted - {c.name for c in cases}
        if unknown:
            parser.error(f"unknown cases: {', '.join(sorted(unknown))}")
        cases = [c for c in cases if c.name in wanted]
    if not shutil.which("uv"):
        parser.error("uv is required: https://docs.astral.sh/uv/")
    engines = ENGINES if args.engine == "both" else (args.engine,)

    table: dict[str, dict[str, Result]] = {c.name: {} for c in cases}
    jobs = [(c, e) for c in cases for e in engines]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(run_case, c, e, args.python, args.keep): (c, e) for c, e in jobs
        }
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            table[result.case][result.engine] = result
            _err(
                f"[{done}/{len(jobs)}] {result.case} on {ENGINE_LABELS[result.engine]}:"
                f" {result.status} ({result.seconds:.1f}s)"
            )

    report = render_markdown(cases, table, engines)
    if args.markdown:
        args.markdown.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.json:
        raw = {
            name: {e: asdict(r) for e, r in row.items()} for name, row in table.items()
        }
        args.json.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")

    regressions = [c.name for c in cases if verdict(table[c.name]) == "**regression**"]
    if regressions:
        _err(f"Regressions: {', '.join(regressions)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

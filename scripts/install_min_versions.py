from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def load_min_versions() -> list[str]:
    in_section = False
    dependencies: list[str] = []
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"

    for raw_line in pyproject.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not in_section:
            if line == "min-versions = [":
                in_section = True
            continue
        if line == "]":
            return [entry.replace(" == ", "==") for entry in dependencies]
        if line:
            dependencies.append(line.strip('",'))

    raise RuntimeError("Failed to load min-versions from pyproject.toml")


def main() -> int:
    dependencies = load_min_versions()
    command = [sys.executable, "-m", "pip", "install", "--force-reinstall", *dependencies]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())

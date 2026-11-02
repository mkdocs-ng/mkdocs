"""
Draw the build-time bar chart in the README.

    python -m benchmarks.chart docs/img/build-speed.svg "MkDocs NG=9.3" "Zensical=18.2"

Bars whose label starts with "MkDocs NG" get the brand color; the others are grey.
Writes a light version to the given path and a dark one next to it, with
`-dark` added to the name, for the README's `<picture>`.
"""

from __future__ import annotations

import argparse
import html
import os

THEMES = {
    "": {"text": "#1f2328", "muted": "#59636e", "bar": "#d1d9e0", "brand": "#0061fe"},
    "-dark": {
        "text": "#f0f6fc",
        "muted": "#9198a1",
        "bar": "#3d444d",
        "brand": "#6ea8ff",
    },
}

WIDTH = 720
LABEL_WIDTH = 190
ROW = 34
BAR = 20
TOP = 8


def draw(bars: list[tuple[str, float]], colors: dict[str, str]) -> str:
    longest = max(seconds for _, seconds in bars)
    # Leave room after the longest bar for its time.
    scale = (WIDTH - LABEL_WIDTH - 80) / longest
    height = TOP * 2 + ROW * len(bars)
    font = "font-family=\"-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif\""
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Build times" {font} font-size="14">'
    ]
    for i, (label, seconds) in enumerate(bars):
        y = TOP + i * ROW
        middle = y + ROW / 2
        ours = label.startswith("MkDocs NG")
        fill = colors["brand"] if ours else colors["bar"]
        weight = ' font-weight="600"' if ours else ""
        width = max(seconds * scale, 2)
        lines += [
            f'<text x="{LABEL_WIDTH - 12}" y="{middle}" dy="0.35em" text-anchor="end" '
            f'fill="{colors["text"]}"{weight}>{html.escape(label)}</text>',
            f'<rect x="{LABEL_WIDTH}" y="{middle - BAR / 2}" width="{width:.1f}" height="{BAR}" '
            f'rx="3" fill="{fill}"/>',
            f'<text x="{LABEL_WIDTH + width + 8:.1f}" y="{middle}" dy="0.35em" '
            f'fill="{colors["text"] if ours else colors["muted"]}"{weight}>{seconds:.1f} s</text>',
        ]
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("output", help="path of the light SVG")
    parser.add_argument(
        "bars", nargs="+", help="LABEL=SECONDS, in the order to draw them"
    )
    args = parser.parse_args()
    bars = []
    for spec in args.bars:
        label, _, seconds = spec.rpartition("=")
        bars.append((label, float(seconds)))
    stem, ext = os.path.splitext(args.output)
    for suffix, colors in THEMES.items():
        with open(f"{stem}{suffix}{ext}", "w", encoding="utf-8") as f:
            f.write(draw(bars, colors))


if __name__ == "__main__":
    main()

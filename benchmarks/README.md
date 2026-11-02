# Benchmarks

Two kinds of benchmarks live here.

## Micro-benchmarks

The `test_*.py` files are pytest benchmarks of MkDocs NG itself. CI runs them on
every pull request with [CodSpeed](https://codspeed.io/), which reports any
change in speed:

```bash
hatch run bench:run        # run them once
hatch run bench:codspeed   # as CI does
```

They build the generated site from `corpus.py`, which is the same every run.

## Comparison with other tools

`compare.py` produces the numbers on the
[Comparison](https://mkdocs-ng.org/about/comparison/#build-speed) page: it gives
MkDocs NG and other documentation tools the same Markdown and times them one
after the other on the same machine.

Install each tool in its own environment, so that none of them picks up another
one's packages. For example, with [uv](https://docs.astral.sh/uv/):

```bash
uv venv /tmp/venvs/ng && VIRTUAL_ENV=/tmp/venvs/ng uv pip install mkdocs-ng mkdocs-sumi mkdocs-ng-material
uv venv /tmp/venvs/up && VIRTUAL_ENV=/tmp/venvs/up uv pip install mkdocs==1.6.1 mkdocs-material
uv venv /tmp/venvs/zs && VIRTUAL_ENV=/tmp/venvs/zs uv pip install zensical
uv venv /tmp/venvs/sp && VIRTUAL_ENV=/tmp/venvs/sp uv pip install sphinx myst-parser
```

Write the site, then time the tools. `{out}` is a fresh output directory for
each run:

```bash
python -m benchmarks.compare corpus /tmp/bench/1000 --pages 1000
python -m benchmarks.compare build /tmp/bench/1000 \
    --tool "MkDocs NG=/tmp/venvs/ng/bin/mkdocs build -q -f mkdocs-mkdocs.yml -d {out}" \
    --tool "MkDocs 1.6.1=/tmp/venvs/up/bin/mkdocs build -q -f mkdocs-mkdocs.yml -d {out}"
python -m benchmarks.compare build /tmp/bench/1000 --before "rm -rf site .cache" \
    --tool "Zensical=/tmp/venvs/zs/bin/zensical build -f zensical.yml"
python -m benchmarks.compare build /tmp/bench/1000 --cwd other/sphinx \
    --tool "Sphinx=/tmp/venvs/sp/bin/sphinx-build -q -j 4 -b html docs {out}"
```

`corpus` also writes `mkdocs-material.yml` and `mkdocs-sumi.yml`, and the same
pages as VitePress, Docusaurus and Starlight projects under `other/`; run
`npm install vitepress`, `npm install @docusaurus/core @docusaurus/preset-classic
react react-dom` or `npm install astro @astrojs/starlight sharp` in their
directories first. Install them there rather than linking a `node_modules`
from elsewhere: Docusaurus and Starlight fail to build otherwise.

`--before` runs an untimed command before each run. Use it to clear the caches
that make a build not clean: `.cache` for Zensical, `node_modules/.astro` for
Starlight, `node_modules/.cache` for Docusaurus and `docs/.vitepress/cache` for
VitePress.

To time how long `mkdocs serve` takes to show an edited page:

```bash
python -m benchmarks.compare serve /tmp/bench/1000 \
    --tool "MkDocs NG=/tmp/venvs/ng/bin/mkdocs serve -f mkdocs-mkdocs.yml -a 127.0.0.1:{port}" \
    --tool "Zensical=/tmp/venvs/zs/bin/zensical serve -f zensical.yml -a 127.0.0.1:{port}"
```

A 5,000-page site with Material for MkDocs writes more than 4 GB, because every
page holds the whole navigation; Zensical's cache for it takes another 8 GB.

The bar chart in the project README is drawn from the 1,000-page build times by
`chart.py`, which writes a light and a dark SVG:

```bash
python -m benchmarks.chart docs/img/build-speed.svg "MkDocs NG=11.5" "Zensical=17.4" \
    --title "Clean build of a 1,000-page site" --note "4 cores, median of 3 runs"
```

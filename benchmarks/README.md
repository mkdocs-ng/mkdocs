# Performance benchmarks

This directory contains the performance benchmark suite for the MkDocs build
pipeline, run with [pytest-codspeed] and tracked continuously by
[CodSpeed] in CI (`.github/workflows/codspeed.yml`).

## What is measured

*   `test_build.py` — clean full builds of synthetic sites at several sizes
    (config loading included, matching the `mkdocs serve` rebuild loop), and a
    dirty rebuild (the `--dirty` inner loop).
*   `test_page.py` — a single `Page.render()` call: Markdown parser
    construction, conversion and toc extraction.
*   `test_render.py` — a single page's Jinja template render with a large
    navigation (the O(N²) sitewide term from upstream issue
    mkdocs/mkdocs#3695).
*   `test_search.py` — search index population and serialization.
*   `test_files.py` — file discovery (`get_files`) and navigation
    construction.

The synthetic sites are generated on the fly with realistic Markdown
(headings, prose, fenced code, cross-page and anchor links).

## Running locally

```bash
hatch run bench:test       # smoke run: each benchmark executes once
hatch run bench:codspeed   # measure: prints a wall-time table
```

Site sizes default to 10, 50 and 200 pages. For local scaling studies,
override them via the environment:

```bash
MKDOCS_BENCH_SIZES=100,400,1600 hatch run bench:codspeed benchmarks/test_build.py
```

In CI the same suite runs under CodSpeed's instrumentation, which measures
simulated CPU time deterministically; every pull request gets a report
comparing its performance against `main`.

[pytest-codspeed]: https://github.com/CodSpeedHQ/pytest-codspeed
[CodSpeed]: https://codspeed.io

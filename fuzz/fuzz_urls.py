"""
Fuzz the URL helpers used for every link, asset and nav entry.

Run it with `pip install atheris -e .` and
`python fuzz/fuzz_urls.py -max_total_time=60`.
"""

from __future__ import annotations

import logging
import sys

import atheris

with atheris.instrument_imports():
    from mkdocs import utils

logging.disable(logging.CRITICAL)


def test_one_input(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    url = fdp.ConsumeUnicodeNoSurrogates(64)
    other = fdp.ConsumeUnicodeNoSurrogates(64)
    utils.get_relative_url(url, other)
    utils.normalize_url(url, base=other)
    # These helpers cache every path they see, which is fine for the bounded
    # set of paths in a site but not for millions of random inputs.
    utils._get_norm_url.cache_clear()
    utils._norm_parts.cache_clear()


def main() -> None:
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

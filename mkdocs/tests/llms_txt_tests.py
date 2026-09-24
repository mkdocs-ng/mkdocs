#!/usr/bin/env python

import os
import unittest

from mkdocs.commands import build
from mkdocs.contrib.llms_txt import markdown_path
from mkdocs.structure.files import File
from mkdocs.structure.pages import Page
from mkdocs.tests.base import PathAssertionMixin, dedent, load_config, tempdir

DOCS = {
    "index.md": "---\ndescription: Start here.\n---\n# Welcome\n\nSee [install](guide/install.md).\n",
    "guide/install.md": "Install with `pip`.\n\nBack [home](../index.md).\n",
    "guide/advanced.md": "# Advanced [beta]\n\nText.\n",
    "draft.md": "# Draft\n",
}
NAV = [
    {"Home": "index.md"},
    {
        "Guide": [
            {"Installation": "guide/install.md"},
            {"More": ["guide/advanced.md"]},
        ]
    },
    {"External": "https://example.org/"},
]


def _read(site_dir, path):
    with open(os.path.join(site_dir, path), encoding="utf-8") as f:
        return f.read()


class LlmsTxtPluginTests(PathAssertionMixin, unittest.TestCase):
    @tempdir(files=DOCS)
    @tempdir()
    def test_build(self, site_dir, docs_dir):
        cfg = load_config(
            docs_dir=docs_dir,
            site_dir=site_dir,
            site_description="A demo site.",
            nav=NAV,
            draft_docs="draft.md",
            plugins=["llms_txt"],
        )
        build.build(cfg)

        self.assertEqual(
            _read(site_dir, "llms.txt"),
            dedent(
                r"""
                # Example

                > A demo site.

                ## Pages

                - [Home](index.md): Start here.

                ## Guide

                - [Installation](guide/install.md)

                ## Guide / More

                - [Advanced \[beta\]](guide/advanced.md)
                """
            )
            + "\n",
        )
        # Front matter is stripped, and relative links still work.
        self.assertEqual(
            _read(site_dir, "index.md"),
            "# Welcome\n\nSee [install](guide/install.md).\n",
        )
        # A page without a heading of its own gets its title.
        self.assertEqual(
            _read(site_dir, "guide/install.md"),
            "# Installation\n\nInstall with `pip`.\n\nBack [home](../index.md).\n",
        )
        self.assertPathIsFile(site_dir, "guide/advanced.md")
        self.assertPathNotExists(site_dir, "draft.md")
        self.assertPathNotExists(site_dir, "llms-full.txt")

    @tempdir(files=DOCS)
    @tempdir()
    def test_build_full_output(self, site_dir, docs_dir):
        cfg = load_config(
            docs_dir=docs_dir,
            site_dir=site_dir,
            nav=NAV,
            draft_docs="draft.md",
            plugins={"llms_txt": {"full_output": True}},
        )
        build.build(cfg)

        self.assertEqual(
            _read(site_dir, "llms-full.txt"),
            dedent(
                """
                # Example

                # Welcome

                See [install](guide/install.md).

                # Installation

                Install with `pip`.

                Back [home](../index.md).

                # Advanced [beta]

                Text.
                """
            )
            + "\n",
        )

    @tempdir(files={"index.md": "# Home\n", "my page.md": "# My page\n"})
    @tempdir()
    def test_build_site_url(self, site_dir, docs_dir):
        cfg = load_config(
            docs_dir=docs_dir,
            site_dir=site_dir,
            site_url="https://example.com/docs/",
            plugins=["llms_txt"],
        )
        build.build(cfg)

        self.assertEqual(
            _read(site_dir, "llms.txt"),
            dedent(
                """
                # Example

                ## Pages

                - [Home](https://example.com/docs/index.md)
                - [My page](https://example.com/docs/my%20page.md)
                """
            )
            + "\n",
        )
        self.assertPathIsFile(site_dir, "my page.md")

    def test_markdown_path(self):
        cfg = load_config()
        for src_uri, expected in [
            ("index.md", "index.md"),
            ("foo/bar.md", "foo/bar.md"),
            ("foo/bar.markdown", "foo/bar.md"),
            ("README.md", "README.md"),
        ]:
            with self.subTest(src_uri):
                file = File(
                    src_uri, cfg.docs_dir, cfg.site_dir, use_directory_urls=True
                )
                self.assertEqual(markdown_path(Page(None, file, cfg)), expected)

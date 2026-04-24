#!/usr/bin/env python

from __future__ import annotations

import importlib.util
import types
import unittest
from pathlib import Path

from mkdocs.tests.base import dedent


def _load_docs_hooks():
    hooks_path = Path(__file__).resolve().parents[2] / "docs" / "hooks.py"
    spec = importlib.util.spec_from_file_location("docs_hooks", hooks_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DocsHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hooks = _load_docs_hooks()

    def test_release_notes_links_switch_repo_after_fork(self):
        markdown = dedent(
            """
            # Release Notes

            ## Version 1.7.0 (2026-04-23)

            * Current release fix #4
            * Compare: https://github.com/mkdocs/mkdocs/compare/1.6.1...1.7.0

            ## Version 1.6.1 (2024-08-30)

            * Previous release fix #3795 and (#3809)
            * Compare: https://github.com/mkdocs-ng/mkdocs/compare/1.6.0...1.6.1
            * Existing link: [#3629](https://github.com/mkdocs-ng/mkdocs/issues/3629)

            ```text
            #9999
            https://github.com/mkdocs-ng/mkdocs/issues/9999
            ```
            """
        )
        page = types.SimpleNamespace(
            file=types.SimpleNamespace(src_uri="about/release-notes.md")
        )
        config = types.SimpleNamespace(
            config_file_path=str(Path("mkdocs.yml").resolve())
        )

        rendered = self.hooks.on_page_markdown(markdown, page=page, config=config)

        assert rendered is not None
        self.assertIn("[#4](https://github.com/mkdocs-ng/mkdocs/issues/4)", rendered)
        self.assertIn(
            "https://github.com/mkdocs-ng/mkdocs/compare/1.6.1...1.7.0", rendered
        )
        self.assertIn("[#3795](https://github.com/mkdocs/mkdocs/issues/3795)", rendered)
        self.assertIn(
            "([#3809](https://github.com/mkdocs/mkdocs/issues/3809))", rendered
        )
        self.assertIn(
            "https://github.com/mkdocs/mkdocs/compare/1.6.0...1.6.1", rendered
        )
        self.assertIn("[#3629](https://github.com/mkdocs/mkdocs/issues/3629)", rendered)
        self.assertIn(
            "```text\n#9999\nhttps://github.com/mkdocs-ng/mkdocs/issues/9999\n```",
            rendered,
        )

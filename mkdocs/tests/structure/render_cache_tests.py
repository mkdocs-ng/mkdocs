from __future__ import annotations

import unittest
from unittest import mock

import markdown

from mkdocs.structure import render_cache
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.tests.structure.page_tests import DOCS_DIR, load_config


class UnknownExtension(markdown.Extension):
    def extendMarkdown(self, md):
        pass


def makeExtension(**kwargs):
    return UnknownExtension(**kwargs)


class RenderCacheTests(unittest.TestCase):
    def setUp(self):
        self.cache = render_cache.RenderCache()
        patcher = mock.patch.object(render_cache, "active", self.cache)
        patcher.start()
        self.addCleanup(patcher.stop)

    def build(self, content, files=("index.md", "other.md"), add_extension=None, **cfg):
        """One "build": fresh config, files and page, like a serve rebuild."""
        self.cache.start_build()
        config = load_config(docs_dir=DOCS_DIR, **cfg)
        if add_extension is not None:
            # What a plugin does in `on_config`.
            config.markdown_extensions.append(add_extension)
        fs = Files(
            [
                File(f, config.docs_dir, config.site_dir, config.use_directory_urls)
                for f in files
            ]
        )
        page = Page(None, fs.get_file_from_path("index.md"), config)
        page.markdown = content
        with mock.patch.object(
            Page, "_convert", autospec=True, side_effect=Page._convert
        ) as conv:
            page.render(config, fs)
        return page, conv.call_count, fs

    def test_unchanged_page_is_not_converted_again(self):
        md = "# Title\n\n## Part\n\n[other](other.md#part)"
        first, calls1, _ = self.build(md, validation={"anchors": "info"})
        second, calls2, fs = self.build(md, validation={"anchors": "info"})
        self.assertEqual((calls1, calls2), (1, 0))
        self.assertEqual(second.content, first.content)
        self.assertEqual(second.title, "Title")
        self.assertEqual([t.title for t in second.toc], ["Title"])
        self.assertEqual([t.title for t in list(second.toc)[0].children], ["Part"])
        self.assertIsNot(second.toc, first.toc)
        self.assertEqual(second.present_anchor_ids, {"title", "part"})
        # Links point at this build's File objects.
        self.assertEqual(
            second.links_to_anchors,
            {fs.get_file_from_path("other.md"): {"part": "other.md#part"}},
        )

    def test_changed_markdown_is_converted(self):
        self.build("# One")
        page, calls, _ = self.build("# Two")
        self.assertEqual(calls, 1)
        self.assertEqual(page.title, "Two")

    def test_changed_files_are_converted(self):
        first, _, _ = self.build("[x](new.md)")
        second, calls, _ = self.build("[x](new.md)", files=("index.md", "new.md"))
        self.assertEqual(calls, 1)
        self.assertIn('href="new/"', second.content)
        self.assertNotIn('href="new/"', first.content)

    def test_changed_config_is_converted(self):
        self.build("# One")
        _, calls, _ = self.build("# One", use_directory_urls=False)
        self.assertEqual(calls, 1)
        _, calls, _ = self.build(
            "# One", markdown_extensions=[{"toc": {"permalink": True}}]
        )
        self.assertEqual(calls, 1)

    def test_warnings_are_logged_again(self):
        self.build("[x](missing.md)")
        with self.assertLogs("mkdocs.structure.pages") as cm:
            _, calls, _ = self.build("[x](missing.md)")
        self.assertEqual(calls, 0)
        self.assertIn("missing.md", cm.output[0])

    def test_unknown_extensions_disable_the_cache(self):
        ext = [__name__]
        self.build("# One", markdown_extensions=ext)
        _, calls, _ = self.build("# One", markdown_extensions=ext)
        self.assertEqual(calls, 1)

    def test_known_extension_by_class_path(self):
        ext = ["markdown.extensions.toc:TocExtension"]
        self.build("# One", markdown_extensions=ext)
        _, calls, _ = self.build("# One", markdown_extensions=ext)
        self.assertEqual(calls, 0)

    def test_extension_instances_disable_the_cache(self):
        from markdown.extensions.toc import TocExtension

        self.build("# One", add_extension=TocExtension())
        _, calls, _ = self.build("# One", add_extension=TocExtension())
        self.assertEqual(calls, 1)

    def test_unused_entries_are_dropped(self):
        self.build("# One")
        self.build("# Two")
        self.build("# Three")
        self.assertEqual(len(self.cache._entries), 2)

    def test_inactive_outside_serve(self):
        with mock.patch.object(render_cache, "active", None):
            config = load_config(docs_dir=DOCS_DIR)
            fs = Files([File("index.md", config.docs_dir, config.site_dir, True)])
            page = Page(None, fs.get_file_from_path("index.md"), config)
            page.markdown = "# One"
            page.render(config, fs)
        self.assertEqual(page.title, "One")
        self.assertEqual(self.cache._entries, {})


class RenderCacheBuildTests(unittest.TestCase):
    """Rebuilds with the cache give the same site and the same warnings."""

    DOCS = {
        "index.md": "# Home\n\n[Guide](guide/index.md) [Gone](gone.md)\n\n## Part {#part}",
        "guide/index.md": "# Guide\n\n- [Home](../index.md#part)\n- [Bad](../index.md#nope)",
        "guide/page.md": "---\ntitle: Meta title\n---\n\nText[^1].\n\n[^1]: Note.\n\n| a | b |\n| - | - |\n| 1 | 2 |",
    }

    def _build(self, docs_dir, site_dir):
        import logging
        import os
        import re

        from mkdocs.commands.build import build
        from mkdocs.tests.base import load_config as base_load_config

        cfg = base_load_config(
            docs_dir=docs_dir,
            site_dir=site_dir,
            markdown_extensions=[
                "toc",
                "admonition",
                "footnotes",
                "tables",
                "attr_list",
            ],
            validation={"anchors": "warn"},
        )
        logger = logging.getLogger("mkdocs")
        with self.assertLogs(logger, level="WARNING") as cm:
            build(cfg)
        out = {}
        for root, _, names in os.walk(site_dir):
            for name in names:
                if name.endswith(".html"):
                    path = os.path.join(root, name)
                    with open(path, encoding="utf-8") as f:
                        out[os.path.relpath(path, site_dir)] = re.sub(
                            r"Build Date UTC : .*", "", f.read()
                        )
        return out, sorted(cm.output)

    def test_same_site_and_warnings(self):
        import tempfile

        from mkdocs.tests.base import tempdir

        @tempdir(files=self.DOCS)
        def run(self, docs_dir):
            with tempfile.TemporaryDirectory() as tmp:
                with mock.patch.object(render_cache, "active", None):
                    plain = self._build(docs_dir, f"{tmp}/a")
                cache = render_cache.RenderCache()
                with mock.patch.object(render_cache, "active", cache):
                    cache.start_build()
                    cold = self._build(docs_dir, f"{tmp}/b")
                    cache.start_build()
                    with mock.patch.object(Page, "_convert", autospec=True) as conv:
                        warm = self._build(docs_dir, f"{tmp}/c")
                    self.assertEqual(conv.call_count, 0)
            self.assertEqual(len(plain[1]), 2, plain[1])
            self.assertEqual(cold, plain)
            self.assertEqual(warm, plain)

        run(self)

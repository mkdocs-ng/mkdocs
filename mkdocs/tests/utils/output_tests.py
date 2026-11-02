#!/usr/bin/env python

from __future__ import annotations

import os
import unittest
from unittest import mock

from mkdocs import utils
from mkdocs.commands import build
from mkdocs.config.base import load_config as load_config_file
from mkdocs.tests.base import load_config, tempdir
from mkdocs.utils import output


class SiteOutputTests(unittest.TestCase):
    def setUp(self):
        self.site_output = output.SiteOutput()
        patcher = mock.patch.object(output, "active", self.site_output)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_build(self, site_dir, files, *, success=True):
        """Write `files` like one build would, and return how many were written."""
        written = 0
        real_open = open

        def counting_open(path, mode="r", *args, **kwargs):
            nonlocal written
            if "w" in mode:
                written += 1
            return real_open(path, mode, *args, **kwargs)

        self.assertTrue(self.site_output.start_build(site_dir))
        with mock.patch("builtins.open", counting_open):
            for name, content in files.items():
                utils.write_file(content, os.path.join(site_dir, name))
        self.site_output.end_build(success=success)
        return written

    @tempdir()
    def test_unchanged_files_are_not_written_again(self, site_dir):
        files = {"index.html": b"home", "a/index.html": b"a"}
        self.assertEqual(self.run_build(site_dir, files), 2)
        self.assertEqual(self.run_build(site_dir, files), 0)
        files["a/index.html"] = b"changed"
        self.assertEqual(self.run_build(site_dir, files), 1)
        with open(os.path.join(site_dir, "a", "index.html"), "rb") as f:
            self.assertEqual(f.read(), b"changed")

    @tempdir()
    def test_file_changed_on_disk_is_written_again(self, site_dir):
        files = {"index.html": b"home"}
        self.run_build(site_dir, files)
        # Like a plugin that minifies the output in `on_post_build`.
        with open(os.path.join(site_dir, "index.html"), "wb") as f:
            f.write(b"minified")
        self.assertEqual(self.run_build(site_dir, files), 1)
        with open(os.path.join(site_dir, "index.html"), "rb") as f:
            self.assertEqual(f.read(), b"home")

    @tempdir()
    def test_deleted_file_is_written_again(self, site_dir):
        files = {"index.html": b"home"}
        self.run_build(site_dir, files)
        os.remove(os.path.join(site_dir, "index.html"))
        self.assertEqual(self.run_build(site_dir, files), 1)

    @tempdir()
    def test_stale_files_and_empty_dirs_are_removed(self, site_dir):
        self.run_build(site_dir, {"index.html": b"home", "old/page/index.html": b"old"})
        self.run_build(site_dir, {"index.html": b"home"})
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "index.html")))
        self.assertFalse(os.path.exists(os.path.join(site_dir, "old")))
        self.assertTrue(os.path.isdir(site_dir))

    @tempdir()
    def test_other_files_are_left_alone(self, site_dir):
        self.run_build(site_dir, {"index.html": b"home"})
        # Written by a plugin without `utils.write_file`.
        with open(os.path.join(site_dir, "plugin.txt"), "w") as f:
            f.write("x")
        self.run_build(site_dir, {})
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "plugin.txt")))
        self.assertFalse(os.path.exists(os.path.join(site_dir, "index.html")))

    @tempdir()
    @tempdir()
    def test_files_outside_site_dir_are_not_tracked(self, site_dir, other_dir):
        outside = os.path.join(other_dir, "cache.json")
        self.assertTrue(self.site_output.start_build(site_dir))
        utils.write_file(b"{}", outside)
        self.site_output.end_build(success=True)
        self.run_build(site_dir, {})
        self.assertTrue(os.path.isfile(outside))

    @tempdir()
    def test_failed_build_removes_nothing(self, site_dir):
        self.run_build(site_dir, {"index.html": b"home", "a.html": b"a"})
        self.run_build(site_dir, {"index.html": b"home"}, success=False)
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "a.html")))
        # The next successful build removes what neither of them produced.
        self.run_build(site_dir, {"b.html": b"b"})
        self.assertEqual(sorted(os.listdir(site_dir)), ["b.html"])

    @tempdir()
    def test_nested_build_writes_as_usual(self, site_dir):
        self.assertTrue(self.site_output.start_build(site_dir))
        self.assertTrue(self.site_output.building)
        self.assertFalse(self.site_output.start_build(site_dir))
        self.assertFalse(self.site_output.building)
        self.site_output.end_build(success=True)
        self.assertTrue(self.site_output.building)
        self.site_output.end_build(success=True)
        self.assertFalse(self.site_output.building)

    @tempdir()
    def test_languages_count_as_one_build(self, site_dir):
        def build_languages(pages):
            self.site_output.start_languages(site_dir)
            for name, content in pages.items():
                self.run_build(
                    os.path.dirname(os.path.join(site_dir, name)),
                    {os.path.basename(name): content},
                )
            self.site_output.end_languages(success=True)

        build_languages({"index.html": b"en", "zh/index.html": b"zh", "old.html": b"o"})
        build_languages({"index.html": b"en", "zh/index.html": b"zh"})
        self.assertEqual(sorted(os.listdir(site_dir)), ["index.html", "zh"])
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "zh", "index.html")))


class ServeBuildTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(output, "active", output.SiteOutput())
        patcher.start()
        self.addCleanup(patcher.stop)

    @tempdir(files={"index.md": "# Home", "old.md": "# Old", "img.png": "png"})
    @tempdir()
    def test_rebuild_keeps_unchanged_files_and_removes_stale_ones(
        self, site_dir, docs_dir
    ):
        cfg = dict(docs_dir=docs_dir, site_dir=site_dir, plugins=[])
        build.build(load_config(**cfg))
        index = os.path.join(site_dir, "index.html")
        mtime = os.stat(index).st_mtime_ns
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "old", "index.html")))

        os.remove(os.path.join(docs_dir, "old.md"))
        os.remove(os.path.join(docs_dir, "img.png"))
        build.build(load_config(**cfg))
        self.assertFalse(os.path.exists(os.path.join(site_dir, "old")))
        self.assertFalse(os.path.exists(os.path.join(site_dir, "img.png")))
        # The home page lost a nav entry, so it was written again; the theme's
        # files didn't change.
        self.assertNotEqual(os.stat(index).st_mtime_ns, mtime)
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "css", "base.css")))

    @tempdir(files={"index.md": "# Home"})
    @tempdir()
    def test_rebuild_without_changes_writes_no_page(self, site_dir, docs_dir):
        cfg = dict(docs_dir=docs_dir, site_dir=site_dir, plugins=["search"])

        def written_files():
            return {
                os.path.join(root, name): os.stat(os.path.join(root, name)).st_mtime_ns
                for root, _, names in os.walk(site_dir)
                for name in names
                # Theme and media files are copied again, which is cheap.
                if name.endswith((".html", ".json", ".xml"))
            }

        build.build(load_config(**cfg))
        before = written_files()
        self.assertIn(os.path.join(site_dir, "index.html"), before)
        self.assertIn(os.path.join(site_dir, "search", "search_index.json"), before)
        build.build(load_config(**cfg))
        self.assertEqual(written_files(), before)

    @tempdir(
        files={
            "mkdocs.yml": "site_name: Test\nplugins: []\nlanguages:\n  en: English\n  zh: 中文\n",
            "docs/index.md": "# Home",
            "docs/index.zh.md": "# 首页",
            "docs/guide.md": "# Guide",
        }
    )
    @tempdir()
    def test_rebuild_of_multi_language_site_keeps_every_language(self, site_dir, tdir):
        def rebuild():
            build.build(
                load_config_file(os.path.join(tdir, "mkdocs.yml"), site_dir=site_dir)
            )

        rebuild()
        rebuild()
        for path in (
            "index.html",
            "guide/index.html",
            "zh/index.html",
            "zh/guide/index.html",
        ):
            self.assertTrue(os.path.isfile(os.path.join(site_dir, path)), path)
        os.remove(os.path.join(tdir, "docs", "guide.md"))
        rebuild()
        self.assertFalse(os.path.exists(os.path.join(site_dir, "guide")))
        self.assertFalse(os.path.exists(os.path.join(site_dir, "zh", "guide")))
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "zh", "index.html")))

    @tempdir(files={"index.md": "# Home"})
    @tempdir()
    def test_dirty_build_does_not_remove_files(self, site_dir, docs_dir):
        cfg = dict(docs_dir=docs_dir, site_dir=site_dir, plugins=[])
        build.build(load_config(**cfg))
        with open(os.path.join(site_dir, "extra.html"), "w") as f:
            f.write("x")
        with self.assertLogs("mkdocs", "WARNING"):
            build.build(load_config(**cfg), dirty=True)
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "extra.html")))

    @tempdir(files={"index.md": "# Home"})
    @tempdir()
    def test_build_without_serve_cleans_site_dir(self, site_dir, docs_dir):
        with open(os.path.join(site_dir, "stale.html"), "w") as f:
            f.write("x")
        with mock.patch.object(output, "active", None):
            build.build(load_config(docs_dir=docs_dir, site_dir=site_dir, plugins=[]))
        self.assertFalse(os.path.exists(os.path.join(site_dir, "stale.html")))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

import jinja2
import markdown

from mkdocs.structure import render_cache
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.tests.base import load_config as load_site_config
from mkdocs.tests.structure.page_tests import DOCS_DIR, load_config


class UnknownExtension(markdown.Extension):
    def extendMarkdown(self, md):
        pass


def makeExtension(**kwargs):
    return UnknownExtension(**kwargs)


class CacheableExtension(markdown.Extension):
    mkdocs_cacheable = True

    def __init__(self, **kwargs):
        self.config = {"word": ["x", "A word."]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        pass


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

    def test_unrelated_files_keep_the_cache(self):
        md = "[x](other.md)"
        self.build(md)
        # A page added, then one removed: the link resolves as before.
        _, calls, _ = self.build(md, files=("index.md", "other.md", "new.md"))
        self.assertEqual(calls, 0)
        page, calls, _ = self.build(md, files=("index.md", "other.md"))
        self.assertEqual(calls, 0)
        self.assertIn('href="other/"', page.content)

    def test_removed_link_target_is_converted(self):
        self.build("[x](other.md)")
        with self.assertLogs("mkdocs.structure.pages") as cm:
            page, calls, _ = self.build("[x](other.md)", files=("index.md",))
        self.assertEqual(calls, 1)
        self.assertIn("other.md", cm.output[0])
        self.assertNotIn('href="other/"', page.content)

    def test_moved_link_target_is_converted(self):
        self.build("[x](other.md)", use_directory_urls=False)
        files = [
            File("index.md", "/docs", "/site", False),
            File("other.md", "/docs", "/site", False, dest_uri="moved.html"),
        ]
        self.cache.start_build()
        config = load_config(docs_dir=DOCS_DIR, use_directory_urls=False)
        fs = Files(files)
        page = Page(None, fs.get_file_from_path("index.md"), config)
        page.markdown = "[x](other.md)"
        page.render(config, fs)
        self.assertIn('href="moved.html"', page.content)

    def test_new_suggestion_is_converted(self):
        # The warning for a broken link suggests a file that exists.
        with self.assertLogs("mkdocs.structure.pages") as cm:
            self.build("[x](new)", files=("index.md",))
        self.assertNotIn("Did you mean", cm.output[0])
        with self.assertLogs("mkdocs.structure.pages") as cm:
            _, calls, _ = self.build("[x](new)", files=("index.md", "new.md"))
        self.assertEqual(calls, 1)
        self.assertIn("Did you mean 'new.md'?", cm.output[0])

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

    def test_extension_module_can_opt_in(self):
        ext = [__name__]
        with mock.patch(f"{__name__}.mkdocs_cacheable", True, create=True):
            self.build("# One", markdown_extensions=ext)
            _, calls, _ = self.build("# One", markdown_extensions=ext)
        self.assertEqual(calls, 0)

    def test_extension_class_can_opt_in(self):
        ext = [f"{__name__}:CacheableExtension"]
        self.build("# One", markdown_extensions=ext)
        _, calls, _ = self.build("# One", markdown_extensions=ext)
        self.assertEqual(calls, 0)

    def test_cacheable_extension_instance(self):
        self.build("# One", add_extension=CacheableExtension(word="a"))
        _, calls, _ = self.build("# One", add_extension=CacheableExtension(word="a"))
        self.assertEqual(calls, 0)
        # Its config is part of the key.
        _, calls, _ = self.build("# One", add_extension=CacheableExtension(word="b"))
        self.assertEqual(calls, 1)

    def test_missing_extension_module_disables_the_cache(self):
        self.assertFalse(render_cache._is_cacheable("no_such_module_for_mkdocs"))
        self.assertFalse(render_cache._is_cacheable(f"{__name__}:NoSuchClass"))

    def test_sumi_extension_is_known(self):
        self.assertTrue(render_cache._is_cacheable("mkdocs_sumi.markdown.extension"))

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


class PageCacheTests(unittest.TestCase):
    """The theme's HTML of a page is reused by serve rebuilds when its context is the same."""

    def setUp(self):
        from mkdocs.utils import output

        self.cache = render_cache.RenderCache()
        self.site_output = output.SiteOutput()
        for target, value in (
            (render_cache, self.cache),
            (output, self.site_output),
        ):
            patcher = mock.patch.object(target, "active", value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, path, text):
        full = os.path.join(self.tdir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        # A different mtime even on file systems with a coarse clock.
        st = os.stat(full)
        os.utime(full, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9 * len(self.renders)))

    def read(self, path):
        with open(os.path.join(self.tdir, "site", path), encoding="utf-8") as f:
            return f.read()

    def build(self, **cfg):
        """One serve rebuild; returns the source files of the pages that were rendered."""
        from mkdocs.commands.build import build

        self.cache.start_build()
        config = load_site_config(
            config_file_path=os.path.join(self.tdir, "mkdocs.yml"),
            docs_dir=os.path.join(self.tdir, "docs"),
            site_dir=os.path.join(self.tdir, "site"),
            **cfg,
        )
        rendered = []
        real_render = jinja2.Template.render

        def render(template, *args, **kwargs):
            context = args[0] if args else kwargs
            if template.name == "main.html" and context.get("page") is not None:
                rendered.append(context["page"].file.src_uri)
            return real_render(template, *args, **kwargs)

        with mock.patch.object(jinja2.Template, "render", render):
            build(config, serve_url="http://127.0.0.1:8000/")
        self.renders.append(sorted(rendered))
        return sorted(rendered)

    def run_in_tempdir(self, test):
        with tempfile.TemporaryDirectory(prefix="mkdocs_test-") as tdir:
            self.tdir = tdir
            self.renders = []
            self.write("docs/index.md", "# Home\n\nWelcome")
            self.write("docs/other.md", "# Other\n\nText")
            test()

    def test_unchanged_pages_are_not_rendered_again(self):
        def test():
            self.assertEqual(self.build(), ["index.md", "other.md"])
            before = self.read("index.html")
            self.write("docs/other.md", "# Other\n\nNew text")
            self.assertEqual(self.build(), ["other.md"])
            self.assertEqual(self.read("index.html"), before)
            self.assertIn("New text", self.read("other/index.html"))

        self.run_in_tempdir(test)

    def test_title_change_renders_every_page(self):
        def test():
            self.build()
            self.write("docs/other.md", "# Renamed\n\nText")
            self.assertEqual(self.build(), ["index.md", "other.md"])
            self.assertIn("Renamed", self.read("index.html"))

        self.run_in_tempdir(test)

    def test_changed_template_renders_every_page(self):
        def test():
            self.write("theme/main.html", "{% extends 'base.html' %}")
            theme = {"name": "mkdocs", "custom_dir": os.path.join(self.tdir, "theme")}
            self.build(theme=theme)
            self.assertEqual(self.build(theme=theme), [])
            self.write(
                "theme/main.html",
                "{% extends 'base.html' %}{% block footer %}NEW FOOTER{% endblock %}",
            )
            self.assertEqual(self.build(theme=theme), ["index.md", "other.md"])
            self.assertIn("NEW FOOTER", self.read("index.html"))

        self.run_in_tempdir(test)

    def test_new_template_override_renders_every_page(self):
        def test():
            os.makedirs(os.path.join(self.tdir, "theme"))
            theme = {"name": "mkdocs", "custom_dir": os.path.join(self.tdir, "theme")}
            self.build(theme=theme)
            self.write("theme/main.html", "OVERRIDDEN {{ page.title }}")
            self.assertEqual(self.build(theme=theme), ["index.md", "other.md"])
            self.assertEqual(self.read("index.html"), "OVERRIDDEN Home")

        self.run_in_tempdir(test)

    def test_unknown_objects_in_the_context_disable_the_reuse(self):
        def test():
            self.write(
                "hooks.py",
                "class Thing:\n"
                "    pass\n"
                "def on_page_context(context, page, **kwargs):\n"
                "    context['thing'] = Thing()\n",
            )
            self.build(hooks=["hooks.py"])
            self.assertEqual(self.build(hooks=["hooks.py"]), ["index.md", "other.md"])

        self.run_in_tempdir(test)

    def test_plugin_events_run_for_reused_pages(self):
        def test():
            self.write(
                "hooks.py",
                "import itertools\n"
                "counter = itertools.count()\n"
                "def on_page_context(context, page, **kwargs):\n"
                "    page.meta['seen'] = True\n"
                "def on_post_page(output, page, **kwargs):\n"
                "    return output + f'<!-- {next(counter)} -->'\n",
            )
            self.build(hooks=["hooks.py"])
            first = self.read("index.html")
            self.assertEqual(self.build(hooks=["hooks.py"]), [])
            # `post_page` ran again on the reused HTML.
            self.assertNotEqual(self.read("index.html"), first)

        self.run_in_tempdir(test)

    def test_attributes_set_by_plugins_are_part_of_the_key(self):
        def test():
            self.write(
                "hooks.py",
                "import itertools\n"
                "counter = itertools.count()\n"
                "def on_page_content(html, page, **kwargs):\n"
                "    page.custom = next(counter)\n",
            )
            self.build(hooks=["hooks.py"])
            self.assertEqual(self.build(hooks=["hooks.py"]), ["index.md", "other.md"])

        self.run_in_tempdir(test)

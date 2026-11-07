#!/usr/bin/env python

import json
import os
import unittest
from unittest import mock

from mkdocs.config.config_options import ValidationError
from mkdocs.contrib import search
from mkdocs.contrib.search import search_index
from mkdocs.structure.files import File
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc
from mkdocs.tests.base import dedent, get_markdown_toc, load_config


def strip_whitespace(string):
    return string.replace("\n", "").replace(" ", "")


class SearchConfigTests(unittest.TestCase):
    def test_lang_default(self):
        option = search.LangOption(default=["en"])
        value = option.validate(None)
        self.assertEqual(["en"], value)

    def test_lang_str(self):
        option = search.LangOption()
        value = option.validate("en")
        self.assertEqual(["en"], value)

    def test_lang_list(self):
        option = search.LangOption()
        value = option.validate(["en"])
        self.assertEqual(["en"], value)

    def test_lang_multi_list(self):
        option = search.LangOption()
        value = option.validate(["en", "es", "fr"])
        self.assertEqual(["en", "es", "fr"], value)

    def test_lang_no_default_none(self):
        option = search.LangOption()
        value = option.validate(None)
        self.assertIsNone(value)

    def test_lang_no_default_str(self):
        option = search.LangOption(default=[])
        value = option.validate("en")
        self.assertEqual(["en"], value)

    def test_lang_no_default_list(self):
        option = search.LangOption(default=[])
        value = option.validate(["en"])
        self.assertEqual(["en"], value)

    def test_lang_bad_type(self):
        option = search.LangOption()
        with self.assertRaises(ValidationError):
            option.validate({})

    def test_lang_bad_code(self):
        option = search.LangOption()
        value = option.validate(["foo"])
        self.assertEqual(["en"], value)

    def test_lang_good_and_bad_code(self):
        option = search.LangOption()
        value = option.validate(["en", "foo"])
        self.assertEqual(["en"], value)

    def test_lang_missing_and_with_territory(self):
        option = search.LangOption()
        value = option.validate(["cs_CZ", "pt_BR", "fr"])
        self.assertEqual(["fr", "en", "pt"], value)


class SearchPluginTests(unittest.TestCase):
    def test_plugin_config_defaults(self):
        expected = {
            "lang": None,
            "separator": r"[\s\-]+",
            "stop_words": False,
            "min_search_length": 3,
            "prebuild_index": False,
            "indexing": "full",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_plugin_config_lang(self):
        expected = {
            "lang": ["es"],
            "separator": r"[\s\-]+",
            "stop_words": False,
            "min_search_length": 3,
            "prebuild_index": False,
            "indexing": "full",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({"lang": "es"})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_plugin_config_separator(self):
        expected = {
            "lang": None,
            "separator": r"[\s\-\.]+",
            "stop_words": False,
            "min_search_length": 3,
            "prebuild_index": False,
            "indexing": "full",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({"separator": r"[\s\-\.]+"})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_plugin_config_stop_words(self):
        expected = {
            "lang": None,
            "separator": r"[\s\-]+",
            "stop_words": True,
            "min_search_length": 3,
            "prebuild_index": False,
            "indexing": "full",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({"stop_words": True})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_plugin_config_min_search_length(self):
        expected = {
            "lang": None,
            "separator": r"[\s\-]+",
            "stop_words": False,
            "min_search_length": 2,
            "prebuild_index": False,
            "indexing": "full",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({"min_search_length": 2})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_plugin_config_prebuild_index(self):
        expected = {
            "lang": None,
            "separator": r"[\s\-]+",
            "stop_words": False,
            "min_search_length": 3,
            "prebuild_index": True,
            "indexing": "full",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({"prebuild_index": True})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_plugin_config_indexing(self):
        expected = {
            "lang": None,
            "separator": r"[\s\-]+",
            "stop_words": False,
            "min_search_length": 3,
            "prebuild_index": False,
            "indexing": "titles",
        }
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({"indexing": "titles"})
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_event_on_config_defaults(self):
        plugin = search.SearchPlugin()
        plugin.load_config({})
        result = plugin.on_config(load_config(theme="mkdocs", extra_javascript=[]))
        self.assertFalse(result["theme"]["search_index_only"])
        self.assertFalse(result["theme"]["include_search_page"])
        self.assertEqual(result["theme"].static_templates, {"404.html", "sitemap.xml"})
        self.assertEqual(len(result["theme"].dirs), 3)
        self.assertEqual(result["extra_javascript"], ["search/main.js"])
        self.assertEqual(plugin.config.lang, [result["theme"]["locale"].language])

    def test_event_on_config_python_prebuild_index(self):
        plugin = search.SearchPlugin()
        plugin.load_config({"prebuild_index": "python"})
        with self.assertLogs("mkdocs.contrib.search", level="INFO") as cm:
            plugin.on_config(load_config(theme="mkdocs", extra_javascript=[]))
        self.assertEqual(
            cm.output,
            [
                (
                    "INFO:mkdocs.contrib.search:The 'python' method of the search plugin's "
                    "'prebuild_index' config option is pending deprecation and will not be "
                    "supported in a future release."
                )
            ],
        )

    def test_event_on_config_lang(self):
        plugin = search.SearchPlugin()
        plugin.load_config({"lang": "es"})
        result = plugin.on_config(load_config(theme="mkdocs", extra_javascript=[]))
        self.assertFalse(result["theme"]["search_index_only"])
        self.assertFalse(result["theme"]["include_search_page"])
        self.assertEqual(result["theme"].static_templates, {"404.html", "sitemap.xml"})
        self.assertEqual(len(result["theme"].dirs), 3)
        self.assertEqual(result["extra_javascript"], ["search/main.js"])
        self.assertEqual(plugin.config.lang, ["es"])

    def test_event_on_config_theme_locale(self):
        plugin = search.SearchPlugin()
        plugin.load_config({})
        result = plugin.on_config(
            load_config(theme={"name": "mkdocs", "locale": "fr"}, extra_javascript=[])
        )
        self.assertFalse(result["theme"]["search_index_only"])
        self.assertFalse(result["theme"]["include_search_page"])
        self.assertEqual(result["theme"].static_templates, {"404.html", "sitemap.xml"})
        self.assertEqual(len(result["theme"].dirs), 3)
        self.assertEqual(result["extra_javascript"], ["search/main.js"])
        self.assertEqual(plugin.config.lang, [result["theme"]["locale"].language])

    def test_event_on_config_include_search_page(self):
        plugin = search.SearchPlugin()
        plugin.load_config({})
        config = load_config(
            theme={"name": "mkdocs", "include_search_page": True}, extra_javascript=[]
        )
        result = plugin.on_config(config)
        self.assertFalse(result["theme"]["search_index_only"])
        self.assertTrue(result["theme"]["include_search_page"])
        self.assertEqual(
            result["theme"].static_templates, {"404.html", "sitemap.xml", "search.html"}
        )
        self.assertEqual(len(result["theme"].dirs), 3)
        self.assertEqual(result["extra_javascript"], ["search/main.js"])

    def test_event_on_config_search_index_only(self):
        plugin = search.SearchPlugin()
        plugin.load_config({})
        config = load_config(
            theme={"name": "mkdocs", "search_index_only": True}, extra_javascript=[]
        )
        result = plugin.on_config(config)
        self.assertTrue(result["theme"]["search_index_only"])
        self.assertFalse(result["theme"]["include_search_page"])
        self.assertEqual(result["theme"].static_templates, {"404.html", "sitemap.xml"})
        self.assertEqual(len(result["theme"].dirs), 2)
        self.assertEqual(len(result["extra_javascript"]), 0)

    @mock.patch("mkdocs.utils.write_file", autospec=True)
    @mock.patch("mkdocs.utils.copy_file", autospec=True)
    def test_event_on_post_build_defaults(self, mock_copy_file, mock_write_file):
        plugin = search.SearchPlugin()
        plugin.load_config({})
        config = load_config(theme="mkdocs")
        plugin.on_config(config)
        plugin.on_pre_build(config)
        plugin.on_post_build(config)
        self.assertEqual(mock_copy_file.call_count, 0)
        self.assertEqual(mock_write_file.call_count, 1)

    @mock.patch("mkdocs.utils.write_file", autospec=True)
    @mock.patch("mkdocs.utils.copy_file", autospec=True)
    def test_event_on_post_build_single_lang(self, mock_copy_file, mock_write_file):
        plugin = search.SearchPlugin()
        plugin.load_config({"lang": ["es"]})
        config = load_config(theme="mkdocs")
        plugin.on_pre_build(config)
        plugin.on_post_build(config)
        self.assertEqual(mock_copy_file.call_count, 2)
        self.assertEqual(mock_write_file.call_count, 1)

    @mock.patch("mkdocs.utils.write_file", autospec=True)
    @mock.patch("mkdocs.utils.copy_file", autospec=True)
    def test_event_on_post_build_multi_lang(self, mock_copy_file, mock_write_file):
        plugin = search.SearchPlugin()
        plugin.load_config({"lang": ["es", "fr"]})
        config = load_config(theme="mkdocs")
        plugin.on_pre_build(config)
        plugin.on_post_build(config)
        self.assertEqual(mock_copy_file.call_count, 4)
        self.assertEqual(mock_write_file.call_count, 1)

    @mock.patch("mkdocs.utils.write_file", autospec=True)
    @mock.patch("mkdocs.utils.copy_file", autospec=True)
    def test_event_on_post_build_japanese(self, mock_copy_file, mock_write_file):
        plugin = search.SearchPlugin()
        plugin.load_config({"lang": ["ja"]})
        config = load_config(theme="mkdocs")
        plugin.on_pre_build(config)
        plugin.on_post_build(config)
        # Japanese also needs the TinySegmenter word splitter.
        self.assertEqual(
            [os.path.basename(c.args[1]) for c in mock_copy_file.call_args_list],
            ["lunr.stemmer.support.js", "tinyseg.js", "cjk-segment.js", "lunr.ja.js"],
        )
        self.assertEqual(mock_write_file.call_count, 1)

    @mock.patch("mkdocs.utils.write_file", autospec=True)
    @mock.patch("mkdocs.utils.copy_file", autospec=True)
    def test_event_on_post_build_chinese(self, mock_copy_file, mock_write_file):
        plugin = search.SearchPlugin()
        plugin.load_config({"lang": ["en", "zh"]})
        config = load_config(theme="mkdocs")
        plugin.on_pre_build(config)
        plugin.on_post_build(config)
        # Chinese needs the word splitter, also next to other languages.
        self.assertEqual(
            [os.path.basename(c.args[1]) for c in mock_copy_file.call_args_list],
            [
                "lunr.stemmer.support.js",
                "lunr.multi.js",
                "cjk-segment.js",
                "lunr.zh.js",
            ],
        )

    @mock.patch("mkdocs.utils.write_file", autospec=True)
    @mock.patch("mkdocs.utils.copy_file", autospec=True)
    def test_event_on_post_build_search_index_only(
        self, mock_copy_file, mock_write_file
    ):
        plugin = search.SearchPlugin()
        plugin.load_config({"lang": ["es"]})
        config = load_config(theme={"name": "mkdocs", "search_index_only": True})
        plugin.on_pre_build(config)
        plugin.on_post_build(config)
        self.assertEqual(mock_copy_file.call_count, 0)
        self.assertEqual(mock_write_file.call_count, 1)


class FastParseTests(unittest.TestCase):
    """The fast parser must find exactly what `ContentParser` finds, or give up."""

    def assertSameAsContentParser(self, content, *, fast=True):
        parser = search_index.ContentParser()
        parser.feed(content)
        parser.close()
        parsed = search_index._fast_parse(content)
        if not fast:
            self.assertIsNone(parsed, content)
            return
        self.assertIsNotNone(parsed, content)
        assert parsed is not None
        self.assertEqual(parsed.stripped_html, parser.stripped_html, content)
        self.assertEqual(
            [(d.id, d.title, d.text) for d in parsed.data],
            [(d.id, d.title, d.text) for d in parser.data],
            content,
        )

    def test_markdown_output(self):
        for content in (
            "",
            "Plain text",
            '<h1 id="title">Title</h1>\n<p>Text &amp; more &lt;b&gt; &copy; &#169; &#xa9;</p>',
            "<p>Before</p><h2>No id</h2><p>One</p><p>Two\n</p>\n",
            '<H2 ID="Upper">Mixed <em>case</em></H2><P>x</P>',
            '<h3 id=bare class="a b">Bare id</h3>',
            "<h3 id='single' id=\"twice\">Last id wins</h3>",
            '<h2 id="a&amp;b">Escaped id</h2>',
            "<h2 id>Empty id</h2>after",
            "<h2/>self-closing<h3 />too",
            '<p><a href="x.md" title="a>b">link</a><br><br/><img alt="1 &lt; 2" src="i.png" /></p>',
            '<table><tr><th>A</th></tr><tr><td>1</td></tr></table><h6 id="z">Z</h6>end',
            '<div\nclass="wrapped"\n>text</div >',
            "<h1>Unclosed",
            "text with &amp trailing & ampersands &",
        ):
            with self.subTest(content=content):
                self.assertSameAsContentParser(content)

    def test_other_html_is_left_to_content_parser(self):
        for content in (
            "1 < 2",
            "a <3",
            "<!-- comment -->",
            "<!DOCTYPE html>",
            "<?php ?>",
            "<script>var a = '<h1>x</h1>';</script>",
            "<style>h1 > p {}</style>",
            "<textarea><h1>x</h1></textarea>",
            "<title>T</title>",
            '<p title="unclosed>text</p>',
            "</ h1>",
            "<p =x>",
        ):
            with self.subTest(content=content):
                self.assertSameAsContentParser(content, fast=False)

    def test_random_markup(self):
        import random

        rng = random.Random(4)
        pieces = [
            "<h1>",
            "</h1>",
            '<h2 id="x">',
            "</h2>",
            "<h3 id=y>",
            "</h3>",
            "<p>",
            "</p>",
            "<br>",
            "<br/>",
            "<em>",
            "</em>",
            '<a href="u">',
            "</a>",
            "text",
            " ",
            "\n",
            "&amp;",
            "&lt;",
            "&nbsp;",
            "&#62;",
            "&bogus;",
            "&",
            "word\n",
            "<code>",
            "</code>",
            "<",
            ">",
            '"',
            "<!-- c -->",
        ]
        for _ in range(3000):
            content = "".join(rng.choices(pieces, k=rng.randint(1, 25)))
            parsed = search_index._fast_parse(content)
            with self.subTest(content=content):
                self.assertSameAsContentParser(content, fast=parsed is not None)


class SearchIndexTests(unittest.TestCase):
    def test_html_stripping(self):
        stripper = search_index.ContentParser()

        stripper.feed("<h1>Testing</h1><p>Content</p>")

        self.assertEqual(stripper.stripped_html, "Testing\nContent")

    def test_content_parser(self):
        parser = search_index.ContentParser()

        parser.feed('<h1 id="title">Title</h1>TEST')
        parser.close()

        self.assertEqual(
            parser.data,
            [search_index.ContentSection(text=["TEST"], id_="title", title="Title")],
        )

    def test_content_parser_no_id(self):
        parser = search_index.ContentParser()

        parser.feed("<h1>Title</h1>TEST")
        parser.close()

        self.assertEqual(
            parser.data,
            [search_index.ContentSection(text=["TEST"], id_=None, title="Title")],
        )

    def test_content_parser_content_before_header(self):
        parser = search_index.ContentParser()

        parser.feed("Content Before H1 <h1>Title</h1>TEST")
        parser.close()

        self.assertEqual(
            parser.data,
            [search_index.ContentSection(text=["TEST"], id_=None, title="Title")],
        )

    def test_content_parser_no_sections(self):
        parser = search_index.ContentParser()

        parser.feed("No H1 or H2<span>Title</span>TEST")

        self.assertEqual(parser.data, [])

    def test_find_toc_by_id(self):
        """Test finding the relevant TOC item by the tag ID."""
        index = search_index.SearchIndex()

        md = dedent(
            """
            # Heading 1
            ## Heading 2
            ### Heading 3
            """
        )
        toc = get_toc(get_markdown_toc(md))

        toc_item = index._find_toc_by_id(toc, "heading-1")
        self.assertEqual(toc_item.url, "#heading-1")
        self.assertEqual(toc_item.title, "Heading 1")

        toc_item2 = index._find_toc_by_id(toc, "heading-2")
        self.assertEqual(toc_item2.url, "#heading-2")
        self.assertEqual(toc_item2.title, "Heading 2")

        toc_item3 = index._find_toc_by_id(toc, "heading-3")
        self.assertEqual(toc_item3.url, "#heading-3")
        self.assertEqual(toc_item3.title, "Heading 3")

        self.assertIsNone(index._find_toc_by_id(toc, "heading-4"))

    def test_entries_of_unchanged_pages_are_reused_in_serve(self):
        from mkdocs.structure import render_cache

        cfg = load_config()
        md = "# Heading 1\n## Heading 2\n"
        plugin = search.SearchPlugin()
        plugin.load_config({})

        def index_page(content, title="Home"):
            page = Page(title, File("index.md", cfg.docs_dir, cfg.site_dir, True), cfg)
            page.markdown = md
            page.toc = get_toc(get_markdown_toc(md))
            page.content = content
            index = search_index.SearchIndex(**plugin.config)
            index.add_entry_from_context(page)
            return index._entries

        html = '<h1 id="heading-1">Heading 1</h1><p>One</p><h2 id="heading-2">Heading 2</h2><p>Two</p>'
        with mock.patch.object(
            render_cache, "active", render_cache.RenderCache()
        ) as cache:
            first = index_page(html)
            cache.start_build()
            with mock.patch.object(
                search_index, "_parse_content", side_effect=AssertionError
            ):
                second = index_page(html)
            self.assertEqual(second, first)
            self.assertIsNot(second[0], first[0])
            cache.start_build()
            changed = index_page(html.replace("Two", "Three"))
            self.assertIn("Three", changed[0]["text"])
            cache.start_build()
            retitled = index_page(html, title="Other")
            self.assertEqual(retitled[0]["title"], "Other")
        # Outside of serve, every page is parsed.
        self.assertEqual(index_page(html), first)

    def test_create_search_index(self):
        html_content = """
        <h1 id="heading-1">Heading 1</h1>
        <p>Content 1</p>
        <h2 id="heading-2">Heading 2</h1>
        <p>Content 2</p>
        <h3 id="heading-3">Heading 3</h1>
        <p>Content 3</p>
        """

        base_cfg = load_config()
        pages = [
            Page(
                "Home",
                File(
                    "index.md",
                    base_cfg.docs_dir,
                    base_cfg.site_dir,
                    base_cfg.use_directory_urls,
                ),
                base_cfg,
            ),
            Page(
                "About",
                File(
                    "about.md",
                    base_cfg.docs_dir,
                    base_cfg.site_dir,
                    base_cfg.use_directory_urls,
                ),
                base_cfg,
            ),
        ]

        md = dedent(
            """
            # Heading 1
            ## Heading 2
            ### Heading 3
            """
        )
        toc = get_toc(get_markdown_toc(md))

        full_content = "".join(f"Heading{i}Content{i}" for i in range(1, 4))

        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({})

        for page in pages:
            # Fake page.read_source() and page.render()
            page.markdown = md
            page.toc = toc
            page.content = html_content

            index = search_index.SearchIndex(**plugin.config)
            index.add_entry_from_context(page)

            self.assertEqual(len(index._entries), 4)

            loc = page.url

            self.assertEqual(index._entries[0]["title"], page.title)
            self.assertEqual(strip_whitespace(index._entries[0]["text"]), full_content)
            self.assertEqual(index._entries[0]["location"], loc)

            self.assertEqual(index._entries[1]["title"], "Heading 1")
            self.assertEqual(index._entries[1]["text"], "Content 1")
            self.assertEqual(index._entries[1]["location"], f"{loc}#heading-1")

            self.assertEqual(index._entries[2]["title"], "Heading 2")
            self.assertEqual(strip_whitespace(index._entries[2]["text"]), "Content2")
            self.assertEqual(index._entries[2]["location"], f"{loc}#heading-2")

            self.assertEqual(index._entries[3]["title"], "Heading 3")
            self.assertEqual(strip_whitespace(index._entries[3]["text"]), "Content3")
            self.assertEqual(index._entries[3]["location"], f"{loc}#heading-3")

    def test_search_indexing_options(self):
        def test_page(title, filename, config):
            test_page = Page(
                title,
                File(
                    filename,
                    config.docs_dir,
                    config.site_dir,
                    config.use_directory_urls,
                ),
                config,
            )
            test_page.content = """
                <h1 id="heading-1">Heading 1</h1>
                <p>Content 1</p>
                <h2 id="heading-2">Heading 2</h1>
                <p>Content 2</p>
                <h3 id="heading-3">Heading 3</h1>
                <p>Content 3</p>"""
            test_page.markdown = dedent(
                """
                # Heading 1
                ## Heading 2
                ### Heading 3"""
            )
            test_page.toc = get_toc(get_markdown_toc(test_page.markdown))
            return test_page

        def validate_full(data, page):
            self.assertEqual(len(data), 4)
            for x in data:
                self.assertTrue(x["title"])
                self.assertTrue(x["text"])

        def validate_sections(data, page):
            # Sanity
            self.assertEqual(len(data), 4)
            # Page
            self.assertEqual(data[0]["title"], page.title)
            self.assertFalse(data[0]["text"])
            # Headings
            for x in data[1:]:
                self.assertTrue(x["title"])
                self.assertFalse(x["text"])

        def validate_titles(data, page):
            # Sanity
            self.assertEqual(len(data), 1)
            for x in data:
                self.assertFalse(x["text"])

        for option, validate in {
            "full": validate_full,
            "sections": validate_sections,
            "titles": validate_titles,
        }.items():
            with self.subTest(option):
                plugin = search.SearchPlugin()

                # Load plugin config, overriding indexing for test case
                errors, warnings = plugin.load_config({"indexing": option})
                self.assertEqual(errors, [])
                self.assertEqual(warnings, [])

                base_cfg = load_config(plugins=["search"])
                base_cfg.plugins["search"].config.indexing = option

                pages = [
                    test_page("Home", "index.md", base_cfg),
                    test_page("About", "about.md", base_cfg),
                ]

                for page in pages:
                    index = search_index.SearchIndex(**plugin.config)
                    index.add_entry_from_context(page)
                    data = index.generate_search_index()
                    validate(json.loads(data)["docs"], page)

    @mock.patch("subprocess.Popen", autospec=True)
    def test_prebuild_index(self, mock_popen):
        # See https://stackoverflow.com/a/36501078/866026
        mock_popen.return_value = mock.Mock()
        mock_popen_obj = mock_popen.return_value
        mock_popen_obj.communicate.return_value = ('{"mock": "index"}', None)
        mock_popen_obj.returncode = 0

        index = search_index.SearchIndex(prebuild_index=True)
        expected = {
            "docs": [],
            "config": {"prebuild_index": True},
            "index": {"mock": "index"},
        }
        result = json.loads(index.generate_search_index())
        self.assertEqual(mock_popen.call_count, 1)
        self.assertEqual(mock_popen_obj.communicate.call_count, 1)
        self.assertEqual(result, expected)

    @mock.patch("subprocess.Popen", autospec=True)
    def test_prebuild_index_returns_error(self, mock_popen):
        # See https://stackoverflow.com/a/36501078/866026
        mock_popen.return_value = mock.Mock()
        mock_popen_obj = mock_popen.return_value
        mock_popen_obj.communicate.return_value = ("", "Some Error")
        mock_popen_obj.returncode = 0

        index = search_index.SearchIndex(prebuild_index=True)
        expected = {
            "docs": [],
            "config": {"prebuild_index": True},
        }
        with self.assertLogs("mkdocs") as cm:
            result = json.loads(index.generate_search_index())
        self.assertEqual(
            "\n".join(cm.output),
            "WARNING:mkdocs.contrib.search.search_index:Failed to pre-build search index. Error: Some Error",
        )

        self.assertEqual(mock_popen.call_count, 1)
        self.assertEqual(mock_popen_obj.communicate.call_count, 1)
        self.assertEqual(result, expected)

    @mock.patch("subprocess.Popen", autospec=True)
    def test_prebuild_index_raises_ioerror(self, mock_popen):
        # See https://stackoverflow.com/a/36501078/866026
        mock_popen.return_value = mock.Mock()
        mock_popen_obj = mock_popen.return_value
        mock_popen_obj.communicate.side_effect = OSError
        mock_popen_obj.returncode = 1

        index = search_index.SearchIndex(prebuild_index=True)
        expected = {
            "docs": [],
            "config": {"prebuild_index": True},
        }
        with self.assertLogs("mkdocs") as cm:
            result = json.loads(index.generate_search_index())
        self.assertEqual(
            "\n".join(cm.output),
            "WARNING:mkdocs.contrib.search.search_index:Failed to pre-build search index. Error: ",
        )

        self.assertEqual(mock_popen.call_count, 1)
        self.assertEqual(mock_popen_obj.communicate.call_count, 1)
        self.assertEqual(result, expected)

    @mock.patch("subprocess.Popen", autospec=True, side_effect=OSError)
    def test_prebuild_index_raises_oserror(self, mock_popen):
        # See https://stackoverflow.com/a/36501078/866026
        mock_popen.return_value = mock.Mock()
        mock_popen_obj = mock_popen.return_value
        mock_popen_obj.communicate.return_value = ("foo", "bar")
        mock_popen_obj.returncode = 0

        index = search_index.SearchIndex(prebuild_index=True)
        expected = {
            "docs": [],
            "config": {"prebuild_index": True},
        }
        with self.assertLogs("mkdocs") as cm:
            result = json.loads(index.generate_search_index())
        self.assertEqual(
            "\n".join(cm.output),
            "WARNING:mkdocs.contrib.search.search_index:Failed to pre-build search index. Error: ",
        )

        self.assertEqual(mock_popen.call_count, 1)
        self.assertEqual(mock_popen_obj.communicate.call_count, 0)
        self.assertEqual(result, expected)

    @mock.patch("subprocess.Popen", autospec=True)
    def test_prebuild_index_false(self, mock_popen):
        # See https://stackoverflow.com/a/36501078/866026
        mock_popen.return_value = mock.Mock()
        mock_popen_obj = mock_popen.return_value
        mock_popen_obj.communicate.return_value = ("", "")
        mock_popen_obj.returncode = 0

        index = search_index.SearchIndex(prebuild_index=False)
        expected = {
            "docs": [],
            "config": {"prebuild_index": False},
        }
        result = json.loads(index.generate_search_index())
        self.assertEqual(mock_popen.call_count, 0)
        self.assertEqual(mock_popen_obj.communicate.call_count, 0)
        self.assertEqual(result, expected)

    @unittest.skipUnless(search_index.haslunrpy, "lunr.py is not installed")
    @mock.patch("mkdocs.contrib.search.search_index.lunr", autospec=True)
    def test_prebuild_index_python(self, mock_lunr):
        mock_lunr.return_value.serialize.return_value = {"mock": "index"}
        index = search_index.SearchIndex(prebuild_index="python", lang="en")
        expected = {
            "docs": [],
            "config": {"prebuild_index": "python", "lang": "en"},
            "index": {"mock": "index"},
        }
        result = json.loads(index.generate_search_index())
        self.assertEqual(mock_lunr.call_count, 1)
        self.assertEqual(result, expected)

    @mock.patch("mkdocs.contrib.search.search_index.haslunrpy", False)
    def test_prebuild_index_python_missing_lunr(self):
        # When the lunr.py dependencies are not installed no prebuilt index is created.
        index = search_index.SearchIndex(prebuild_index="python", lang="en")
        expected = {
            "docs": [],
            "config": {"prebuild_index": "python", "lang": "en"},
        }
        with self.assertLogs("mkdocs", level="WARNING"):
            result = json.loads(index.generate_search_index())
        self.assertEqual(result, expected)

    @unittest.skipUnless(search_index.haslunrpy, "lunr.py is not installed")
    def test_prebuild_index_python_stop_words(self):
        from lunr.index import Index  # type: ignore

        def search_prebuilt_index(**config):
            index = search_index.SearchIndex(
                prebuild_index="python", lang=["en"], **config
            )
            index._add_entry("Loops", "Use a while loop for repetition", "loops/")
            result = json.loads(index.generate_search_index())
            lunr_index = Index.load(result["index"])
            return {
                word: [r["ref"] for r in lunr_index.search(word)]
                for word in ("while", "repetition")
            }

        # By default, words like 'while' and 'for' stay searchable.
        self.assertEqual(
            search_prebuilt_index(stop_words=False),
            {"while": ["loops/"], "repetition": ["loops/"]},
        )
        # With `stop_words` enabled, lunr's default stop word filter applies.
        self.assertEqual(
            search_prebuilt_index(stop_words=True),
            {"while": [], "repetition": ["loops/"]},
        )

    @mock.patch("subprocess.Popen", autospec=True)
    def test_prebuild_index_node(self, mock_popen):
        # See https://stackoverflow.com/a/36501078/866026
        mock_popen.return_value = mock.Mock()
        mock_popen_obj = mock_popen.return_value
        mock_popen_obj.communicate.return_value = ('{"mock": "index"}', None)
        mock_popen_obj.returncode = 0

        index = search_index.SearchIndex(prebuild_index="node")
        expected = {
            "docs": [],
            "config": {"prebuild_index": "node"},
            "index": {"mock": "index"},
        }
        result = json.loads(index.generate_search_index())
        self.assertEqual(mock_popen.call_count, 1)
        self.assertEqual(mock_popen_obj.communicate.call_count, 1)
        self.assertEqual(result, expected)

    def test_html_stripped_from_titles(self):
        """HTML tags in page and section titles are stripped from search entries."""
        plugin = search.SearchPlugin()
        errors, warnings = plugin.load_config({})
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        config = load_config(plugins=["search"])
        # A page title with inline HTML from Markdown (e.g. `<code>foo</code>`)
        page = Page(
            "The <code>mkdocs</code> Project",
            File(
                "index.md", config.docs_dir, config.site_dir, config.use_directory_urls
            ),
            config,
        )
        page.content = """
            <h1 id="heading-1">Heading <em>one</em></h1>
            <p>Content</p>"""
        page.markdown = "# Heading 1\n\nContent"
        page.toc = get_toc(get_markdown_toc(page.markdown))

        index = search_index.SearchIndex(**plugin.config)
        index.add_entry_from_context(page)

        self.assertEqual(len(index._entries), 2)
        self.assertEqual(index._entries[0]["title"], "The mkdocs Project")
        self.assertEqual(index._entries[1]["title"], "Heading 1")

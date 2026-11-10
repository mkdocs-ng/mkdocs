#!/usr/bin/env python

from __future__ import annotations

import os
import unittest
from urllib.parse import urljoin

import mkdocs
from mkdocs import languages
from mkdocs.commands.build import build
from mkdocs.config.base import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import Abort, ConfigurationError
from mkdocs.tests.base import tempdir

SUFFIX_SITE = {
    "mkdocs.yml": """
site_name: My Project
site_url: https://example.com/proj/
repo_url: https://github.com/example/proj
edit_uri: edit/main/docs/
plugins: []
languages:
  en: English
  zh:
    name: 简体中文
    site_name: 我的项目
    nav:
      - 首页: index.md
      - 指南: guide.md
      - Other: other.md
nav:
  - Home: index.md
  - Guide: guide.md
  - Other: other.md
""",
    "docs/index.md": "# Home",
    "docs/index.zh.md": "# 首页",
    "docs/guide.md": "# Guide\n\n[Other](other.md)",
    "docs/guide.zh.md": "# 指南\n\n[其他](other.md)",
    "docs/other.md": "# Other\n\n![logo](img/logo.png)",
    "docs/img/logo.png": "png",
}


def _read(*parts: str) -> str:
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


class ParseLanguagesTests(unittest.TestCase):
    def test_forms(self):
        langs = languages.parse_languages(
            {"en": "English", "zh": {"name": "简体中文", "site_name": "X"}, "fr": None}
        )
        self.assertEqual([lang.code for lang in langs], ["en", "zh", "fr"])
        self.assertEqual([lang.name for lang in langs], ["English", "简体中文", "fr"])
        self.assertEqual([lang.path for lang in langs], ["", "zh", "fr"])
        self.assertTrue(langs[0].default)
        self.assertFalse(langs[1].default)
        self.assertEqual(langs[1].overrides, {"site_name": "X"})

    def test_list_form(self):
        langs = languages.parse_languages([{"en": "English"}, "de"])
        self.assertEqual([lang.code for lang in langs], ["en", "de"])

    def test_path_and_fallback(self):
        langs = languages.parse_languages(
            {"en": None, "zh-Hans": {"path": "/cn/", "fallback": False}}
        )
        self.assertEqual(langs[1].path, "cn")
        self.assertFalse(langs[1].fallback)
        self.assertEqual(langs[1].locale, "zh_Hans")

    def test_errors(self):
        for value, message in [
            ([], "at least one"),
            ("en", "Expected a mapping"),
            ({"english": None}, "is not a language code"),
            ({"en": None, "zh": {"site_dir": "x"}}, "can't be set per language"),
            ({"en": {"path": "en"}}, "default language"),
            ({"en": None, "zh": {"path": "a b"}}, "relative URL path"),
            ({"en": None, "zh": {"path": ".."}}, "relative URL path"),
            ({"en": None, "zh": {"path": "../../out"}}, "relative URL path"),
            ({"en": None, "zh": {"path": "zh/./cn"}}, "relative URL path"),
            ({"en": None, "zh": {"path": "."}}, "relative URL path"),
            ({"en": None, "zh": None, "cn": {"path": "zh"}}, "already used"),
            ({"en": None, "zh": {"fallback": "no"}}, "true or false"),
        ]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, message):
                    languages.parse_languages(value)

    def test_link(self):
        link = languages._link
        self.assertEqual(link("", "zh", "guide/"), "zh/guide/")
        self.assertEqual(link("zh", "", "guide/"), "../guide/")
        self.assertEqual(link("zh", "zh", "guide/"), "guide/")
        self.assertEqual(link("zh", "", "./"), "../")
        self.assertEqual(link("", "", "./"), "./")
        self.assertEqual(link("a/b", "c", ""), "../../c/")


class LanguageConfigTests(unittest.TestCase):
    @tempdir(SUFFIX_SITE)
    def test_default_language_config(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        self.assertEqual(cfg.site_name, "My Project")
        self.assertEqual(cfg.theme.locale.language, "en")
        self.assertEqual(cfg.site_dir, os.path.join(tdir, "site"))
        self.assertEqual(languages.current(cfg).code, "en")
        self.assertEqual(
            [lang.docs_dir for lang in cfg.languages], [os.path.join(tdir, "docs")] * 2
        )

    @tempdir(SUFFIX_SITE)
    def test_other_language_config(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        zh = languages.load_language_config(cfg, "zh")
        self.assertEqual(zh.site_name, "我的项目")
        self.assertEqual(zh.theme.locale.language, "zh")
        self.assertEqual(zh.site_dir, os.path.join(tdir, "site", "zh"))
        self.assertEqual(zh.site_url, "https://example.com/proj/zh/")
        self.assertEqual(zh.nav[0], {"首页": "index.md"})
        self.assertEqual(languages.current(zh).code, "zh")

    @tempdir(SUFFIX_SITE)
    def test_settle_site_url(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        zh = languages.load_language_config(cfg, "zh")
        # A plugin such as mike moves the site into a version sub-directory.
        cfg.site_url = urljoin(cfg.site_url, "1.0")
        languages.settle_site_url(cfg)
        self.assertEqual(cfg.site_url, "https://example.com/proj/1.0/")
        zh.site_url = urljoin(zh.site_url, "1.0")
        languages.settle_site_url(zh)
        self.assertEqual(zh.site_url, "https://example.com/proj/1.0/zh/")
        # Unchanged, or changed to somewhere else: left as it is.
        languages.settle_site_url(zh)
        self.assertEqual(zh.site_url, "https://example.com/proj/1.0/zh/")
        zh.site_url = "https://zh.example.com/"
        languages.settle_site_url(zh)
        self.assertEqual(zh.site_url, "https://zh.example.com/")

    @tempdir(SUFFIX_SITE)
    def test_command_line_options_apply_to_every_language(self, tdir):
        out = os.path.join(tdir, "out")
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"), site_dir=out)
        zh = languages.load_language_config(cfg, "zh")
        self.assertEqual(zh.site_dir, os.path.join(out, "zh"))

    @tempdir(SUFFIX_SITE)
    def test_unknown_language(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        with self.assertRaisesRegex(ConfigurationError, "Unknown language 'fr'"):
            languages.load_language_config(cfg, "fr")

    @tempdir(
        {
            "mkdocs.yml": "site_name: X\nplugins: []\ntheme:\n  name: mkdocs\n  locale: en_GB\n"
            "languages:\n  en: English\n  de:\n    theme:\n      locale: de_AT\n",
            "docs/index.md": "",
        }
    )
    def test_theme_locale(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        self.assertEqual(str(cfg.theme.locale), "en_GB")
        de = languages.load_language_config(cfg, "de")
        self.assertEqual(str(de.theme.locale), "de_AT")
        self.assertEqual(de.theme.name, "mkdocs")

    def test_material_theme_language(self):
        def theme_of(theme, code, overrides=None):
            cfg = MkDocsConfig()
            zh = {"name": "中文", **(overrides or {})}
            cfg.load_dict({"theme": theme, "languages": {"en": None, "pt-BR": zh}})
            languages.apply_language(cfg, code)
            return cfg["theme"]

        self.assertEqual(theme_of("material", "pt-BR")["language"], "pt-BR")
        self.assertEqual(theme_of("material", "pt-BR")["locale"], "pt_BR")
        self.assertEqual(theme_of("material", None)["language"], "en")
        # An explicit language is kept: the default language's, or the override.
        material_de = {"name": "material", "language": "de"}
        self.assertEqual(theme_of(material_de, None)["language"], "de")
        self.assertEqual(theme_of(material_de, "pt-BR")["language"], "pt-BR")
        override = {"theme": {"language": "pt"}}
        self.assertEqual(theme_of("material", "pt-BR", override)["language"], "pt")
        # Other themes only get `locale`.
        self.assertNotIn("language", theme_of("mkdocs", "pt-BR"))


class LanguageBuildTests(unittest.TestCase):
    @tempdir(SUFFIX_SITE)
    def test_suffix_build(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        build(cfg)
        site = os.path.join(tdir, "site")
        self.assertIn('<h1 id="home">Home</h1>', _read(site, "index.html"))
        self.assertIn("首页</h1>", _read(site, "zh", "index.html"))
        self.assertIn("指南</h1>", _read(site, "zh", "guide", "index.html"))
        # Untranslated pages fall back to the default language.
        self.assertIn("Other</h1>", _read(site, "zh", "other", "index.html"))
        self.assertTrue(os.path.isfile(os.path.join(site, "zh", "img", "logo.png")))
        # Translations aren't pages of their own.
        self.assertFalse(os.path.exists(os.path.join(site, "index.zh")))
        self.assertFalse(os.path.exists(os.path.join(site, "guide.zh")))
        # The built-in theme's language switcher comes from `extra.alternate`.
        html = _read(site, "zh", "guide", "index.html")
        self.assertIn('lang="zh"', html)
        self.assertIn("我的项目", html)

    @tempdir(SUFFIX_SITE)
    def test_template_context(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        zh = languages.load_language_config(cfg, "zh")
        contexts = {}

        def on_page_context(context, page, **kwargs):
            contexts[page.file.src_uri] = (
                context["i18n"],
                list(zh.extra["alternate"]),
                page.edit_url,
            )
            return context

        zh.plugins.events["page_context"].append(on_page_context)
        cfg._build_languages = ["zh"]
        mkdocs.commands.build._build(zh)

        i18n, alternate, edit_url = contexts["guide.md"]
        self.assertEqual(i18n["language"]["code"], "zh")
        self.assertEqual(i18n["default_language"], "en")
        self.assertFalse(i18n["fallback"])
        self.assertEqual(
            [(x["code"], x["link"], x["current"]) for x in i18n["languages"]],
            [("en", "../guide/", False), ("zh", "guide/", True)],
        )
        self.assertEqual(i18n["languages"][0]["url"], "https://example.com/proj/guide/")
        self.assertEqual(
            alternate,
            [
                {"name": "English", "link": "../guide/", "lang": "en"},
                {"name": "简体中文", "link": "guide/", "lang": "zh"},
            ],
        )
        self.assertEqual(
            edit_url, "https://github.com/example/proj/edit/main/docs/guide.zh.md"
        )
        self.assertTrue(contexts["other.md"][0]["fallback"])

    @tempdir(
        {
            **SUFFIX_SITE,
            "mkdocs.yml": SUFFIX_SITE["mkdocs.yml"].replace(
                "    name: 简体中文\n", "    name: 简体中文\n    fallback: false\n"
            ),
        }
    )
    def test_no_fallback(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        with self.assertLogs("mkdocs") as cm:
            build(cfg)
        site = os.path.join(tdir, "site")
        self.assertFalse(os.path.exists(os.path.join(site, "zh", "other")))
        self.assertTrue(os.path.isfile(os.path.join(site, "zh", "img", "logo.png")))
        self.assertTrue(os.path.isfile(os.path.join(site, "other", "index.html")))
        self.assertIn("'other.md'", "\n".join(cm.output))

    @tempdir(
        {
            "mkdocs.yml": """
site_name: My Project
plugins: []
languages:
  en: English
  zh: 简体中文
""",
            "docs/index.en.md": "# Home",
            "docs/index.zh.md": "# 首页",
            "docs/guide.en.md": "# Guide",
            "docs/guide.md": "# Old guide",
            "docs/changes.md": "# Changes",
        }
    )
    def test_suffixed_default_language(self, tdir):
        # mkdocs-static-i18n sites often name the default language's pages
        # `page.en.md`; other languages fall back to them.
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        build(cfg)
        site = os.path.join(tdir, "site")
        self.assertIn("Home</h1>", _read(site, "index.html"))
        self.assertIn("首页</h1>", _read(site, "zh", "index.html"))
        self.assertIn(">Guide</h1>", _read(site, "guide", "index.html"))
        self.assertIn(">Guide</h1>", _read(site, "zh", "guide", "index.html"))
        self.assertIn("Changes</h1>", _read(site, "zh", "changes", "index.html"))
        self.assertFalse(os.path.exists(os.path.join(site, "zh", "guide.en")))

        zh = languages.load_language_config(cfg, "zh")
        sources = {
            s.src_uri: s
            for s in languages.select_sources(
                zh, zh["languages"][1], lambda d: languages._walk_names(d, set())
            )
        }
        self.assertTrue(sources["guide.md"].is_fallback)
        self.assertTrue(sources["guide.md"].abs_src_path.endswith("guide.en.md"))
        self.assertFalse(sources["index.md"].is_fallback)

    @tempdir(
        {
            "mkdocs.yml": """
site_name: My Project
plugins: []
languages:
  en:
    name: English
    docs_dir: docs/en
  zh:
    name: 简体中文
    docs_dir: docs/zh
""",
            "docs/en/index.md": "# Home",
            "docs/en/guide.en.md": "# Guide",
            "docs/en/intro.md": "# Intro",
            "docs/zh/index.md": "# 首页",
            "docs/zh/intro.md": "# 介绍",
            "docs/zh/intro.en.md": "# Stray intro",
        }
    )
    def test_suffixed_default_language_folders(self, tdir):
        # With a folder per language, the default language's `page.en.md` is
        # still a fallback, but one in another language's folder is ignored.
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        build(cfg)
        site = os.path.join(tdir, "site")
        self.assertIn(">Guide</h1>", _read(site, "zh", "guide", "index.html"))
        self.assertIn("介绍</h1>", _read(site, "zh", "intro", "index.html"))

    @tempdir(
        {
            "mkdocs.yml": """
site_name: My Project
repo_url: https://github.com/example/proj
edit_uri: edit/main/docs/
plugins: []
languages:
  en: English
  zh:
    name: 简体中文
    docs_dir: docs-zh
    edit_uri: edit/main/docs-zh/
""",
            "docs/index.md": "# Home",
            "docs/guide.md": "# Guide",
            "docs/img/logo.png": "png",
            "docs-zh/index.md": "# 首页",
        }
    )
    def test_folder_build(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        zh = languages.load_language_config(cfg, "zh")
        self.assertEqual(zh.docs_dir, os.path.join(tdir, "docs-zh"))
        build(cfg)
        site = os.path.join(tdir, "site")
        self.assertIn("首页</h1>", _read(site, "zh", "index.html"))
        self.assertIn("Guide</h1>", _read(site, "zh", "guide", "index.html"))
        self.assertTrue(os.path.isfile(os.path.join(site, "zh", "img", "logo.png")))
        # The edit link of an untranslated page points to the page that is shown.
        self.assertIn(
            "https://github.com/example/proj/edit/main/docs/guide.md",
            _read(site, "zh", "guide", "index.html"),
        )
        self.assertIn(
            "https://github.com/example/proj/edit/main/docs-zh/index.md",
            _read(site, "zh", "index.html"),
        )

    @tempdir(
        {
            "mkdocs.yml": "site_name: X\nplugins: []\nlanguages:\n  en: English\n"
            "  zh:\n    docs_dir: docs/zh\n",
            "docs/index.md": "# Home",
            "docs/zh/index.md": "# 首页",
        }
    )
    def test_nested_docs_dir_is_not_part_of_the_default_language(self, tdir):
        build(load_config(os.path.join(tdir, "mkdocs.yml")))
        site = os.path.join(tdir, "site")
        self.assertIn("首页</h1>", _read(site, "zh", "index.html"))
        # Not built as pages of the English site at /zh/ first.
        self.assertFalse(os.path.exists(os.path.join(site, "zh", "zh")))

    @tempdir(SUFFIX_SITE)
    def test_site_url_moved_by_plugin(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        zh = languages.load_language_config(cfg, "zh")

        def on_config(config):
            # What mike does to deploy a version.
            config.site_url = urljoin(config.site_url, "1.0")
            return config

        zh.plugins.events["config"].append(on_config)
        mkdocs.commands.build._build(zh)
        site = os.path.join(tdir, "site")
        html = _read(site, "zh", "guide", "index.html")
        self.assertIn(
            '<link rel="canonical" href="https://example.com/proj/1.0/zh/guide/">', html
        )
        self.assertIn(
            "<loc>https://example.com/proj/1.0/zh/guide/</loc>",
            _read(site, "zh", "sitemap.xml"),
        )

    @tempdir(SUFFIX_SITE)
    def test_build_one_language(self, tdir):
        mkdocs.build(os.path.join(tdir, "mkdocs.yml"), language="zh")
        site = os.path.join(tdir, "site")
        self.assertTrue(os.path.isfile(os.path.join(site, "zh", "index.html")))
        self.assertFalse(os.path.isfile(os.path.join(site, "index.html")))
        with self.assertRaisesRegex(Abort, "unknown language 'fr'"):
            mkdocs.build(os.path.join(tdir, "mkdocs.yml"), language="fr")

    @tempdir({"mkdocs.yml": "site_name: X\nplugins: []\n", "docs/index.md": "# Hi"})
    def test_single_language_site(self, tdir):
        cfg = load_config(os.path.join(tdir, "mkdocs.yml"))
        self.assertIsNone(cfg.languages)
        self.assertIsNone(languages.current(cfg))
        build(cfg)
        self.assertTrue(os.path.isfile(os.path.join(tdir, "site", "index.html")))
        with self.assertRaisesRegex(Abort, "no 'languages'"):
            mkdocs.build(os.path.join(tdir, "mkdocs.yml"), language="zh")


if __name__ == "__main__":
    unittest.main()

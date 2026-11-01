import unittest
from textwrap import dedent

import yaml

from mkdocs.tests.base import load_config
from mkdocs.utils import templates


class UtilsTemplatesTests(unittest.TestCase):
    def test_script_tag(self):
        cfg_yaml = dedent(
            """
            extra_javascript:
              - some_plain_javascript.js
              - implicitly_as_module.mjs
              - path: explicitly_as_module.mjs
                type: module
              - path: deferred_plain.js
                defer: true
              - path: scripts/async_module.mjs
                type: module
                async: true
              - path: 'aaaaaa/"my script".mjs'
                type: module
                async: true
                defer: true
              - path: plain.mjs
            """
        )
        config = load_config(**yaml.safe_load(cfg_yaml))
        config.extra_javascript.append("plain_string.mjs")

        self.assertEqual(
            [
                str(
                    templates.script_tag_filter(
                        {"page": None, "base_url": "here"}, item
                    )
                )
                for item in config.extra_javascript
            ],
            [
                '<script src="here/some_plain_javascript.js"></script>',
                '<script src="here/implicitly_as_module.mjs" type="module"></script>',
                '<script src="here/explicitly_as_module.mjs" type="module"></script>',
                '<script src="here/deferred_plain.js" defer></script>',
                '<script src="here/scripts/async_module.mjs" type="module" async></script>',
                '<script src="here/aaaaaa/&#34;my script&#34;.mjs" type="module" defer async></script>',
                '<script src="here/plain.mjs"></script>',
                '<script src="here/plain_string.mjs"></script>',
            ],
        )

    def test_legacy_filters_module(self):
        from mkdocs.utils import filters

        self.assertIs(filters.url_filter, templates.url_filter)


class NavFragmentCacheTests(unittest.TestCase):
    def _env(self):
        import jinja2

        env = jinja2.Environment()
        env.filters["url"] = templates.url_filter
        cache = templates.NavFragmentCache()
        env._mkdocs_nav_fragments = cache
        env.globals["nav_fragment"] = cache
        return env, cache

    def _items(self):
        from types import SimpleNamespace

        page_a = SimpleNamespace(url="a/one/", title="One", active=False, children=None)
        page_b = SimpleNamespace(url="b/two/", title="Two", active=False, children=None)
        section_a = SimpleNamespace(title="A", active=False, children=[page_a])
        section_b = SimpleNamespace(title="B", active=False, children=[page_b])
        return [section_a, section_b], page_a, page_b

    TEMPLATE = (
        "{% for s in nav %}{% call nav_fragment(s) %}"
        "{{ s.title }}{{ counter.append(s.title) or '' }}:"
        "{% for p in s.children %}<a href='{{ p.url|url }}'>{{ p.title }}</a>{% endfor %}"
        "{% endcall %};{% endfor %}"
    )

    def _render(self, env, nav, page, counter, base_url="../.."):
        if page is not None:
            page.active = True
            for section in nav:
                section.active = page in section.children
        try:
            return env.from_string(self.TEMPLATE).render(
                nav=nav, page=page, base_url=base_url, counter=counter
            )
        finally:
            for section in nav:
                section.active = False
            if page is not None:
                page.active = False

    def test_inactive_items_render_once(self):
        env, cache = self._env()
        nav, page_a, page_b = self._items()
        counter = []
        self.assertEqual(
            self._render(env, nav, page_a, counter),
            "A:<a href='./'>One</a>;B:<a href='../../b/two/'>Two</a>;",
        )
        self.assertEqual(
            self._render(env, nav, page_b, counter),
            "A:<a href='../../a/one/'>One</a>;B:<a href='./'>Two</a>;",
        )
        self.assertEqual(
            self._render(env, nav, page_a, counter),
            "A:<a href='./'>One</a>;B:<a href='../../b/two/'>Two</a>;",
        )
        # The active section renders every time, the inactive one only once.
        self.assertEqual(counter, ["A", "B", "A", "B", "A"])

    def test_without_page_uses_base_url(self):
        env, cache = self._env()
        nav, page_a, page_b = self._items()
        counter = []
        self._render(env, nav, page_a, counter)
        self.assertEqual(
            self._render(env, nav, None, counter, base_url="/docs"),
            "A:<a href='/docs/a/one/'>One</a>;B:<a href='/docs/b/two/'>Two</a>;",
        )

    def test_file_urls(self):
        from types import SimpleNamespace

        env, cache = self._env()
        nav, page_a, page_b = self._items()
        page_a.url, page_b.url = "a/one.html", "b/c/two.html"
        index = SimpleNamespace(
            url="index.html", title="Home", active=False, children=None
        )
        counter = []
        self._render(env, nav, page_a, counter)
        self.assertEqual(
            self._render(env, nav, page_b, counter),
            "A:<a href='../../a/one.html'>One</a>;B:<a href='two.html'>Two</a>;",
        )
        self.assertEqual(
            self._render(env, nav, index, counter),
            "A:<a href='a/one.html'>One</a>;B:<a href='b/c/two.html'>Two</a>;",
        )

    def test_new_nav_starts_over(self):
        env, cache = self._env()
        nav, page_a, page_b = self._items()
        counter = []
        self._render(env, nav, page_a, counter)
        nav[1].title = "Renamed"
        self._render(env, list(nav), page_a, counter)
        self.assertEqual(counter, ["A", "B", "A", "Renamed"])

    def test_disabled(self):
        env, cache = self._env()
        cache.enabled = False
        nav, page_a, page_b = self._items()
        counter = []
        self._render(env, nav, page_a, counter)
        self._render(env, nav, page_a, counter)
        self.assertEqual(counter, ["A", "B", "A", "B"])

    def test_section_with_repeated_page_is_not_cached(self):
        from mkdocs.structure.nav import PageAlias
        from mkdocs.structure.pages import Page

        env, cache = self._env()
        nav, page_a, page_b = self._items()
        alias = object.__new__(PageAlias)
        alias._title = None
        alias.page = page_a
        nav[1].children.append(alias)
        self.assertTrue(cache._contains_alias(nav[1]))
        self.assertFalse(cache._contains_alias(nav[0]))
        del Page

    def test_url_filter_outside_fragments(self):
        env, cache = self._env()
        nav, page_a, page_b = self._items()
        self.assertEqual(
            env.from_string("{{ 'b/two/'|url }}").render(page=page_a, base_url="../.."),
            "../../b/two/",
        )


class NavFragmentCacheBuildTests(unittest.TestCase):
    """Built sites must be the same with and without the cache."""

    DOCS = {
        "index.md": "# Home",
        "about.md": "# About",
        "guide/index.md": "# Guide",
        "guide/install.md": "# Install\n\n## Step one\n\n## Step two",
        "guide/usage.md": "# Usage",
        "guide/deep/more.md": "# More",
        "api/index.md": "# API",
        "api/client.md": "# Client",
        "outside/page.md": "# Outside",
    }
    NAV = [
        "index.md",
        {
            "Guide": [
                "guide/index.md",
                "guide/install.md",
                {"Deep": ["guide/deep/more.md"]},
            ]
        },
        {"API": ["api/index.md", "api/client.md", {"Again": "guide/install.md"}]},
        {"Mixed": ["guide/usage.md", "outside/page.md", "about.md#anchor"]},
        {"Links": [{"Example": "https://example.com/"}, {"Root": "/abs/"}]},
    ]

    def _build_all(self, docs_dir, site_dir, **cfg):
        import os
        import re

        from mkdocs.commands.build import build
        from mkdocs.tests.base import load_config

        build(load_config(docs_dir=docs_dir, site_dir=site_dir, **cfg))
        out = {}
        for root, _, names in os.walk(site_dir):
            for name in names:
                if name.endswith(".html"):
                    path = os.path.join(root, name)
                    with open(path, encoding="utf-8") as f:
                        html = re.sub(r"Build Date UTC : .*", "", f.read())
                    out[os.path.relpath(path, site_dir)] = html
        return out

    def test_same_output(self):
        import os
        import tempfile
        from unittest import mock

        from mkdocs.tests.base import tempdir

        @tempdir(files=self.DOCS)
        def run(self, docs_dir):
            for theme in ("mkdocs", "readthedocs"):
                for use_directory_urls in (True, False):
                    for nav in (self.NAV, None):
                        with self.subTest(
                            theme=theme, urls=use_directory_urls, nav=bool(nav)
                        ):
                            cfg = dict(
                                theme={"name": theme},
                                use_directory_urls=use_directory_urls,
                                nav=nav,
                                site_url="https://example.com/docs/",
                            )
                            with (
                                tempfile.TemporaryDirectory() as a,
                                tempfile.TemporaryDirectory() as b,
                            ):
                                cached = self._build_all(docs_dir, a, **cfg)
                                with mock.patch.object(
                                    templates.NavFragmentCache, "enabled", False
                                ):
                                    plain = self._build_all(docs_dir, b, **cfg)
                            self.assertEqual(sorted(cached), sorted(plain))
                            self.assertIn(
                                "index.html" if use_directory_urls else "about.html",
                                {os.path.basename(k) for k in cached},
                            )
                            for name in plain:
                                self.assertEqual(cached[name], plain[name], name)

        run(self)

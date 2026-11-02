#!/usr/bin/env python

import json
import os
import unittest

import yaml

from mkdocs.config import json_schema

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover
    jsonschema = None

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class _AnyTagLoader(yaml.SafeLoader):
    """Load `!ENV`, `!relative` and Python-specific tags as plain values."""


def _construct_any(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node) or "value"
    if isinstance(node, yaml.SequenceNode):
        items = loader.construct_sequence(node)
        return items[-1] if items else "value"
    return loader.construct_mapping(node)


_AnyTagLoader.add_multi_constructor("!", _construct_any)
_AnyTagLoader.add_multi_constructor("tag:yaml.org,2002:python/", _construct_any)


class JSONSchemaTests(unittest.TestCase):
    def test_published_schema_is_up_to_date(self):
        with open(os.path.join(ROOT, "docs", "schema.json"), encoding="utf-8") as f:
            published = f.read()
        self.assertEqual(
            published,
            json_schema.dumps(),
            "docs/schema.json is out of date; run "
            "`python -m mkdocs.config.json_schema > docs/schema.json`",
        )

    def test_every_option_is_described(self):
        schema = json_schema.build_schema()
        missing = [
            name
            for name, prop in schema["properties"].items()
            if not prop.get("description")
        ]
        self.assertEqual(missing, [])


@unittest.skipIf(jsonschema is None, "jsonschema is not installed")
class JSONSchemaValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json_schema.build_schema()
        jsonschema.Draft202012Validator.check_schema(schema)
        cls.validator = jsonschema.Draft202012Validator(schema)

    def assertValid(self, config):
        errors = [
            f"{'/'.join(map(str, e.absolute_path))}: {e.message}"
            for e in self.validator.iter_errors(config)
        ]
        self.assertEqual(errors, [], config)

    def assertInvalid(self, config):
        self.assertFalse(self.validator.is_valid(config), config)

    def test_docs_site_config(self):
        with open(os.path.join(ROOT, "mkdocs.yml"), encoding="utf-8") as f:
            self.assertValid(yaml.load(f, Loader=_AnyTagLoader))

    def test_plugin_compatibility_cases(self):
        with open(os.path.join(ROOT, "compat", "cases.yaml"), encoding="utf-8") as f:
            cases = yaml.load(f, Loader=_AnyTagLoader)
        for case in cases:
            with self.subTest(case["name"]):
                self.assertValid({"site_name": "Test", **case.get("config", {})})

    def test_new_project_configs(self):
        from mkdocs.commands import new

        for text in (new.config_text, new.sumi_config_text):
            self.assertValid(yaml.safe_load(text))

    def test_typical_configs(self):
        self.assertValid({"site_name": "Docs"})
        self.assertValid(
            {
                "site_name": "Docs",
                "INHERIT": ["base.yml", "extra.yml"],
                "theme": {"name": "sumi", "locale": "zh_CN", "palette": "auto"},
                "plugins": [
                    "search",
                    {"llms_txt": {"full_output": True}},
                    {"search": {"lang": ["en", "zh"], "enabled": False}},
                    {"some-third-party-plugin": {"anything": 1}},
                ],
                "nav": [
                    "index.md",
                    {"Guide": ["guide/a.md", {"B": "guide/b.md"}]},
                    {"Link": "https://example.com/"},
                ],
                "extra_javascript": ["a.js", {"path": "b.mjs", "type": "module"}],
                "validation": {"links": {"anchors": "warn"}, "omitted_files": "ignore"},
                "markdown_extensions": [
                    "toc",
                    {"toc": {"permalink": True}},
                    {"admonition": None},
                ],
                "dev_addr": "0.0.0.0:8080",
            }
        )
        self.assertValid(
            {"site_name": "Docs", "plugins": {"search": {}, "other": None}}
        )

    def test_rejects_mistakes(self):
        self.assertInvalid({})  # site_name is required
        self.assertInvalid({"site_name": "Docs", "sitename": "typo"})
        self.assertInvalid({"site_name": "Docs", "use_directory_urls": "yes"})
        self.assertInvalid(
            {"site_name": "Docs", "validation": {"links": {"anchors": "error"}}}
        )
        self.assertInvalid(
            {"site_name": "Docs", "plugins": [{"search": {"min_search_length": "3"}}]}
        )
        self.assertInvalid(
            {"site_name": "Docs", "plugins": [{"llms_txt": {"full": True}}]}
        )
        self.assertInvalid({"site_name": "Docs", "dev_addr": "localhost"})
        self.assertInvalid({"site_name": "Docs", "nav": [{"A": "a.md", "B": "b.md"}]})

    def test_schema_matches_published_url(self):
        with open(os.path.join(ROOT, "docs", "schema.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["$id"], json_schema.SCHEMA_URL)

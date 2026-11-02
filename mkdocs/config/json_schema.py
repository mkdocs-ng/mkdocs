"""
Generate a JSON Schema for `mkdocs.yml` from the config option definitions.

The schema lets editors (through the YAML language server) and coding agents
complete and check `mkdocs.yml` before running a build. It is generated from
`MkDocsConfig` and the configs of the built-in plugins, so it can't drift from
what MkDocs actually accepts. The published copy is `docs/schema.json`;
regenerate it with:

    python -m mkdocs.config.json_schema > docs/schema.json
"""

from __future__ import annotations

import ast
import inspect
import itertools
import json
import sys
import textwrap
from typing import Any

from mkdocs.config import base
from mkdocs.config import config_options as c
from mkdocs.config.defaults import MkDocsConfig, _LogLevel

SCHEMA_URL = "https://mkdocs-ng.github.io/mkdocs/schema.json"
DOCS_URL = "https://mkdocs-ng.github.io/mkdocs/user-guide/configuration/"

# Built-in themes and well-known third-party ones, offered as completions.
# Any other installed theme name is still accepted.
KNOWN_THEMES = ("mkdocs", "readthedocs", "sumi", "material")

# Options that are documented under a heading of their own in the configuration
# guide. Others get no link.
_DOCUMENTED = {
    "site_name",
    "site_url",
    "repo_url",
    "repo_name",
    "edit_uri",
    "edit_uri_template",
    "site_description",
    "site_author",
    "copyright",
    "remote_branch",
    "remote_name",
    "nav",
    "exclude_docs",
    "draft_docs",
    "not_in_nav",
    "validation",
    "theme",
    "docs_dir",
    "site_dir",
    "extra_css",
    "extra_javascript",
    "extra_templates",
    "extra",
    "watch",
    "use_directory_urls",
    "strict",
    "dev_addr",
    "markdown_extensions",
    "hooks",
    "plugins",
}

Schema = dict[str, Any]

# Descriptions for options whose docstring in `MkDocsConfig` is shared with
# another option or missing.
_EXTRA_DOCS = {
    "edit_uri_template": "A template for the edit link of each page, e.g. 'blob/main/docs/{path}'. Use instead of edit_uri when the URL needs more than a prefix.",
    "extra_css": "CSS files from the docs directory (or URLs) to include in every page.",
    "extra_javascript": "JavaScript files from the docs directory (or URLs) to include in every page.",
    "validation": "Log levels for problems found in links and the navigation: warn, info or ignore.",
}


def _attribute_docs(config_class: type) -> dict[str, str]:
    """Return the docstrings written under each attribute of a config class."""
    try:
        source = textwrap.dedent(inspect.getsource(config_class))
    except (OSError, TypeError):
        return {}
    class_def = ast.parse(source).body[0]
    assert isinstance(class_def, ast.ClassDef)
    docs: dict[str, str] = {}
    body = class_def.body
    for node, following in itertools.pairwise(body):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            name = node.targets[0].id
        else:
            continue
        if (
            isinstance(following, ast.Expr)
            and isinstance(following.value, ast.Constant)
            and isinstance(following.value.value, str)
        ):
            docs[name] = " ".join(inspect.cleandoc(following.value.value).split())
    return docs


def _describe(schema: Schema, description: str | None, default: Any = None) -> Schema:
    if description:
        schema = {"description": description, **schema}
    if default is not None and default != [] and default != {}:
        schema["default"] = default
    return schema


_JSON_TYPES = {
    str: "string",
    bool: "boolean",
    int: "integer",
    float: "number",
    list: "array",
    dict: "object",
}

_DEFS: Schema = {
    "navItem": {
        "description": "A page path or URL, or a single-key mapping of a title to a page path, URL or list of nav items.",
        "anyOf": [
            {"type": "string"},
            {
                "type": "object",
                "minProperties": 1,
                "maxProperties": 1,
                "additionalProperties": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"$ref": "#/$defs/navItem"}},
                    ]
                },
            },
        ],
    },
    "extraScript": {
        "anyOf": [
            {"type": "string"},
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "type": {"type": "string"},
                    "async": {"type": "boolean"},
                    "defer": {"type": "boolean"},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        ]
    },
    "markdownExtension": {
        "description": "A Python-Markdown extension name, or a single-key mapping of an extension name to its options.",
        "anyOf": [
            {"type": "string"},
            {
                "type": "object",
                "minProperties": 1,
                "maxProperties": 1,
                "additionalProperties": {"type": ["object", "null"]},
            },
        ],
    },
}


def _option_schema(option: c.BaseConfigOption, docs_hint: str | None = None) -> Schema:
    """Translate one config option into a JSON Schema fragment."""
    schema: Schema
    if isinstance(option, c.Optional):
        return _option_schema(option.option, docs_hint)
    if isinstance(option, c.Deprecated):
        schema = _option_schema(option.option) if option.option else {}
        message = option.message.format(docs_hint) if docs_hint else None
        return {
            **schema,
            "deprecated": True,
            **({"description": message} if message else {}),
        }
    if isinstance(option, _LogLevel):
        return {"type": "string", "enum": list(option.levels)}
    if isinstance(option, c.Choice):
        return {"enum": list(option.choices)}
    if isinstance(option, c.IpAddress):
        return {"type": "string", "pattern": r"^.+:\d+$"}
    if isinstance(option, c.Theme):
        return {
            "anyOf": [
                {"$ref": "#/$defs/themeName"},
                {
                    "type": "object",
                    "properties": {
                        "name": {
                            "anyOf": [{"$ref": "#/$defs/themeName"}, {"type": "null"}],
                            "description": "The name of an installed theme, or null to use only custom_dir.",
                        },
                        "custom_dir": {
                            "type": "string",
                            "description": "A directory of templates and files that override the theme's own.",
                        },
                        "static_templates": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "locale": {
                            "type": "string",
                            "description": "The language of the theme's text, e.g. en or zh_CN.",
                        },
                    },
                    "additionalProperties": True,
                },
            ]
        }
    if isinstance(option, c.Nav):
        return {"type": "array", "items": {"$ref": "#/$defs/navItem"}}
    if isinstance(option, c.MarkdownExtensions):
        return {
            "anyOf": [
                {"type": "array", "items": {"$ref": "#/$defs/markdownExtension"}},
                {
                    "type": "object",
                    "additionalProperties": {"type": ["object", "null"]},
                },
            ]
        }
    if isinstance(option, c.Plugins):
        return {"$ref": "#/$defs/plugins"}
    if isinstance(option, c.ExtraScript):
        return {"$ref": "#/$defs/extraScript"}
    if isinstance(option, c.ListOfItems):
        return {"type": "array", "items": _option_schema(option.option_type)}
    if isinstance(option, c.DictOfItems):
        return {
            "type": "object",
            "additionalProperties": _option_schema(option.option_type),
        }
    if isinstance(option, c.Hooks):
        return {"type": "array", "items": {"type": "string"}}
    if isinstance(option, c.SubConfig):
        config_class = option.config_class
        if not (
            isinstance(config_class, type) and issubclass(config_class, base.Config)
        ):
            return {"type": "object"}
        schema = config_schema(config_class)
        if isinstance(option, c.PropagatingSubConfig):
            # Options of the sub-configs may also be set one level up, for all
            # of them at once (`validation: {anchors: warn}`).
            shortcuts: Schema = {}
            for sub in schema["properties"].values():
                for key, value in sub.get("properties", {}).items():
                    shortcuts.setdefault(key, value)
            schema["properties"] = {**shortcuts, **schema["properties"]}
        return schema
    if isinstance(option, c.Type):
        schema = {"type": _JSON_TYPES.get(option._type, "string")}
        if option._type is list and option.length is not None:
            schema.update(minItems=option.length, maxItems=option.length)
        elif option._type is list and docs_hint in ("extra_css", "extra_templates"):
            schema["items"] = {"type": "string"}
        return schema
    if isinstance(option, (c.URL, c.PathSpec, c.EditURITemplate)):
        return {"type": "string"}
    from mkdocs.contrib.search import LangOption

    if isinstance(option, LangOption):
        return {
            "anyOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}},
            ]
        }
    # An option type this module doesn't know: accept any value rather than
    # reject a valid config.
    return {}


def config_schema(
    config_class: type[base.Config], *, link_docs: bool = False
) -> Schema:
    """Return a JSON Schema for the options of a `Config` subclass."""
    docs = _attribute_docs(config_class)
    if config_class is MkDocsConfig:
        docs.update(_EXTRA_DOCS)
    properties: Schema = {}
    for name, option in config_class._schema:
        if isinstance(option, c.Private) or name == "config_file_path":
            continue
        schema = _option_schema(option, docs_hint=name)
        default = getattr(option, "default", None)
        if isinstance(option, (c.SubConfig, c.Plugins, c.Theme, c.Deprecated)):
            default = None
        schema = _describe(
            schema, docs.get(name) if "description" not in schema else None, default
        )
        if link_docs and name in _DOCUMENTED:
            schema["markdownDescription"] = (
                f"{schema.get('description', '')}\n\n[Documentation]({DOCS_URL}#{name})"
            ).strip()
        properties[name] = schema
    return {"type": "object", "properties": properties, "additionalProperties": False}


def _builtin_plugins() -> dict[str, type[base.Config]]:
    from mkdocs.contrib import llms_txt, search

    return {"search": search._PluginConfig, "llms_txt": llms_txt._PluginConfig}


def _plugins_def() -> Schema:
    known = {}
    for name, config_class in _builtin_plugins().items():
        plugin_schema = config_schema(config_class)
        plugin_schema["properties"]["enabled"] = {
            "type": "boolean",
            "default": True,
            "description": "Set to false to turn the plugin off.",
        }
        known[name] = {"anyOf": [plugin_schema, {"type": "null"}]}
    names = {"anyOf": [{"enum": list(known)}, {"type": "string"}]}
    entry = {
        "anyOf": [
            names,
            {
                "type": "object",
                "minProperties": 1,
                "maxProperties": 1,
                "properties": known,
                "additionalProperties": {"type": ["object", "null"]},
            },
        ]
    }
    return {
        "description": "Plugins, as a list of names or of single-key mappings of a name to its options.",
        "anyOf": [
            {"type": "array", "items": entry},
            {
                "type": "object",
                "properties": known,
                "additionalProperties": {"type": ["object", "null"]},
            },
        ],
    }


def build_schema() -> Schema:
    """Return the JSON Schema of `mkdocs.yml`."""
    root = config_schema(MkDocsConfig, link_docs=True)
    root["properties"]["INHERIT"] = {
        "description": "A config file, or a list of them, to inherit options from.",
        "anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
    }
    root["required"] = ["site_name"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_URL,
        "title": "MkDocs NG configuration (mkdocs.yml)",
        "description": f"See {DOCS_URL}",
        **root,
        "$defs": {
            **_DEFS,
            "themeName": {"anyOf": [{"enum": list(KNOWN_THEMES)}, {"type": "string"}]},
            "plugins": _plugins_def(),
        },
    }


def dumps() -> str:
    return json.dumps(build_schema(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    sys.stdout.write(dumps())

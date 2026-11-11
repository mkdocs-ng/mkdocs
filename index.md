# Home

**Write Markdown. *Ship docs.***

> The maintained MkDocs that keeps your plugins working. One YAML file turns your Markdown into a **fast**, **simple** and **good-looking** documentation site you can host anywhere.

```sh
pip install mkdocs-ng
```

```yaml title="mkdocs.yml"
site_name: My Project

nav:
  - Home: index.md
  - Guide: guide.md

theme:
  name: mkdocs    # or readthedocs, sumi, material...

plugins:
  - search
```

- [Getting Started](getting-started/)
- [Switch from MkDocs](user-guide/migrating/)
- [GitHub](https://github.com/mkdocs-ng/mkdocs)

- **32** Plugins and themes tested
- **20** Upstream bugs fixed
- **3.10+** Python up to 3.15
- **0** Config changes to switch

## Everything a docs site needs, from one YAML file.

- [**Great themes available**](user-guide/choosing-your-theme/): Use a built-in theme, `mkdocs` or `readthedocs`, pick Sumi or one of the many third-party themes, or build your own.
- [**Easy to customize**](user-guide/customizing-your-theme/): Customize your theme, install plugins, change Markdown's behavior with extensions. Many configuration options are available.
- [**Preview as you work**](user-guide/cli/): The built-in dev server shows your documentation as you write it, and reloads the browser whenever you save.
- [**Host anywhere**](user-guide/deploying-your-docs/): MkDocs NG builds a completely static site that you can host on GitHub Pages, Amazon S3, or anywhere else.
- [**Your plugins keep working**](dev-guide/plugins/): Hundreds of plugins and Markdown extensions add API docs, blogs, redirects, diagrams and more. The most popular ones are built against every change.
- [**Written for agents too**](user-guide/configuration/#llmstxt): Every page can have a Markdown copy and the site an `llms.txt`, so coding agents read your docs as easily as people do.

## Good-looking docs out of the box.

Sumi is the theme made for MkDocs NG, and the one this site uses. Install it with `pip install mkdocs-sumi`.

- Search as a command palette: Ctrl K searches every heading.
- Light and dark modes, with fonts, icons and search bundled. No CDN.
- Landing pages, a blog and a releases page from plain Markdown.

- [Sumi documentation](https://sumi.mkdocs-ng.org/)
- [Choosing your theme](user-guide/choosing-your-theme/)

## Switching is a package change.

MkDocs NG keeps the `mkdocs` command, imports and configuration. Your plugins and themes keep working, and bugs that stayed open upstream are fixed. See [how it compares](about/comparison/) to the alternatives.

```sh title="terminal"
pip install -U mkdocs-ng
mkdocs --version
mkdocs serve
```

- [Switching to MkDocs NG](user-guide/migrating/)
- [Fixed upstream issues](about/fixed-upstream-issues/)

## Start writing.

MkDocs NG is free and open source under the BSD 2-Clause license.

- [Getting Started](getting-started/)
- [Release Notes](about/release-notes/)

MkDocs NG is the maintained MkDocs that keeps your plugins working. Already
have a site built with MkDocs? [Switching to MkDocs NG] is a package change:
your configuration, plugins and themes stay the same. See how it [compares] to
the alternatives, or start with the [introductory tutorial] and then the
[User Guide].

[introductory tutorial]: getting-started.md
[User Guide]: user-guide/README.md
[Switching to MkDocs NG]: user-guide/migrating.md
[compares]: about/comparison.md

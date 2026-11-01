---
template: landing.html
title: MkDocs NG
description: Write Markdown. Ship docs. The maintained MkDocs that keeps your plugins working.
hero:
  eyebrow: "MkDocs NG"
  title: "Write Markdown.<br>*Ship docs.*"
  text: "The maintained MkDocs that keeps your plugins working. One YAML file turns your Markdown into a **fast**, **simple** and **good-looking** documentation site you can host anywhere."
  actions:
    - {text: Getting Started, link: getting-started/, icon: rocket, primary: true}
    - {text: Switch from MkDocs, link: user-guide/migrating/, icon: arrow-right-left}
    - {text: GitHub, link: "https://github.com/mkdocs-ng/mkdocs", icon: brand-github}
  install: pip install mkdocs-ng
  code:
    title: mkdocs.yml
    lang: yaml
    content: |
      site_name: My Project

      nav:
        - Home: index.md
        - Guide: guide.md

      theme:
        name: mkdocs    # or readthedocs, sumi, material...

      plugins:
        - search
sections:
  - type: stats
    items:
      - {value: "32", label: Plugins and themes tested}
      - {value: "20", label: Upstream bugs fixed}
      - {value: "3.10+", label: Python up to 3.15}
      - {value: "0", label: Config changes to switch}
  - type: features
    eyebrow: Why MkDocs NG
    title: Everything a docs site needs, from one YAML file.
    items:
      - icon: palette
        title: Great themes available
        text: "Use a built-in theme, `mkdocs` or `readthedocs`, pick Sumi or one of the many third-party themes, or build your own."
        link: user-guide/choosing-your-theme/
      - icon: sliders-horizontal
        title: Easy to customize
        text: Customize your theme, install plugins, change Markdown's behavior with extensions. Many configuration options are available.
        link: user-guide/customizing-your-theme/
      - icon: refresh-cw
        title: Preview as you work
        text: The built-in dev server shows your documentation as you write it, and reloads the browser whenever you save.
        link: user-guide/cli/
      - icon: globe
        title: Host anywhere
        text: MkDocs NG builds a completely static site that you can host on GitHub Pages, Amazon S3, or anywhere else.
        link: user-guide/deploying-your-docs/
      - icon: puzzle
        title: Your plugins keep working
        text: Hundreds of plugins and Markdown extensions add API docs, blogs, redirects, diagrams and more. The most popular ones are built against every change.
        link: dev-guide/plugins/
      - icon: sparkles
        title: Written for agents too
        text: "Every page can have a Markdown copy and the site an `llms.txt`, so coding agents read your docs as easily as people do."
        link: user-guide/configuration/#llmstxt
  - type: split
    eyebrow: Sumi theme
    title: Good-looking docs out of the box.
    text: "Sumi is the theme made for MkDocs NG, and the one this site uses. Install it with `pip install mkdocs-sumi`."
    bullets:
      - "Search as a command palette: <kbd>Ctrl</kbd> <kbd>K</kbd> searches every heading."
      - Light and dark modes, with fonts, icons and search bundled. No CDN.
      - Landing pages, a blog and a releases page from plain Markdown.
    actions:
      - {text: Sumi documentation, link: "https://mkdocs-ng.github.io/mkdocs-sumi/", primary: true}
      - {text: Choosing your theme, link: user-guide/choosing-your-theme/}
    image: img/sumi.png
  - type: split
    reverse: true
    eyebrow: Already on MkDocs?
    title: Switching is a package change.
    text: "MkDocs NG keeps the `mkdocs` command, imports and configuration. Your plugins and themes keep working, and bugs that stayed open upstream are fixed. See [how it compares](about/comparison/) to the alternatives."
    actions:
      - {text: Switching to MkDocs NG, link: user-guide/migrating/, primary: true}
      - {text: Fixed upstream issues, link: about/fixed-upstream-issues/}
    code:
      title: terminal
      lang: sh
      content: |
        pip install -U mkdocs-ng
        mkdocs --version
        mkdocs serve
  - type: cta
    title: Start writing.
    text: MkDocs NG is free and open source under the BSD 2-Clause license.
    actions:
      - {text: Getting Started, link: getting-started/, primary: true}
      - {text: Release Notes, link: about/release-notes/, icon: scroll-text}
---

MkDocs NG is the maintained MkDocs that keeps your plugins working. Already
have a site built with MkDocs? [Switching to MkDocs NG] is a package change:
your configuration, plugins and themes stay the same. See how it [compares] to
the alternatives, or start with the [introductory tutorial] and then the
[User Guide].

[introductory tutorial]: getting-started.md
[User Guide]: user-guide/README.md
[Switching to MkDocs NG]: user-guide/migrating.md
[compares]: about/comparison.md

---
template: landing.html
title: MkDocs
description: Project documentation with Markdown.
hero:
  eyebrow: "MkDocs NG · a maintained MkDocs"
  title: "Project documentation<br>*with Markdown*."
  text: "MkDocs is a **fast**, **simple** and **downright gorgeous** static site generator for project documentation. Write Markdown, configure one YAML file, publish anywhere."
  actions:
    - {text: Getting Started, link: getting-started/, icon: rocket, primary: true}
    - {text: User Guide, link: user-guide/, icon: book-open}
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
        name: mkdocs     # or readthedocs, or any theme

      plugins:
        - search
sections:
  - type: features
    eyebrow: Why MkDocs
    title: Everything a docs site needs, from one YAML file.
    items:
      - icon: palette
        title: Great themes available
        text: "Choose a built-in theme, `mkdocs` or `readthedocs`, pick one of the many third-party themes, or build your own."
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
        text: MkDocs builds a completely static site that you can host on GitHub Pages, Amazon S3, or anywhere else.
        link: user-guide/deploying-your-docs/
      - icon: puzzle
        title: A large plugin ecosystem
        text: Hundreds of plugins and Markdown extensions add API docs, blogs, redirects, diagrams and more.
        link: dev-guide/plugins/
      - icon: sparkles
        title: Written for agents too
        text: "Every page can have a Markdown copy and the site an `llms.txt`, so coding agents read your docs as easily as people do."
        link: user-guide/configuration/#llmstxt
  - type: split
    eyebrow: Already on MkDocs?
    title: Switching is a package change.
    text: "MkDocs NG keeps the `mkdocs` command, imports and configuration. Your plugins and themes keep working."
    actions:
      - {text: Switching to MkDocs NG, link: user-guide/migrating/, primary: true}
      - {text: How it compares, link: about/comparison/}
    code:
      title: terminal
      lang: sh
      content: |
        pip install -U mkdocs-ng
        mkdocs --version
        mkdocs serve
  - type: cta
    title: Start writing.
    text: MkDocs is free and open source under the BSD 2-Clause license.
    actions:
      - {text: Getting Started, link: getting-started/, primary: true}
      - {text: Release Notes, link: about/release-notes/, icon: scroll-text}
---

Already have a site built with MkDocs? [Switching to MkDocs NG] is a package
change: your configuration, plugins and themes stay the same. See how it
[compares] to the alternatives, or start with the [introductory tutorial] and
then the [User Guide].

[introductory tutorial]: getting-started.md
[User Guide]: user-guide/README.md
[Switching to MkDocs NG]: user-guide/migrating.md
[compares]: about/comparison.md

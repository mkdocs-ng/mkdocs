# Versioned Docs

Keep the docs of older releases online, with a menu to switch between versions.

---

MkDocs builds one version of your docs at a time. To publish several, use
[mike]: it builds each version into a folder of its own, such as `1.0/` and
`2.0/`, on the `gh-pages` branch, and writes a `versions.json` file that lists
them for the version menu.

```text
gh-pages branch
    1.0/
    2.0/
    latest -> 2.0
    index.html        # redirects to the default version
    versions.json
```

## Setting up mike

Install mike next to MkDocs NG:

```sh
pip install mkdocs-ng mike
```

mike installs the upstream `mkdocs` package too, as plugins do. MkDocs NG
takes precedence, see [Updating your dependencies](migrating.md#updating-your-dependencies).

mike builds with MkDocs NG even when a plugin, such as `mkdocs-redirects`, has
installed [ProperDocs] too.

Add the `mike` plugin to `mkdocs.yml`, and turn on the version menu of your
theme.

### MkDocs and ReadTheDocs themes

mike adds its version menu to the built-in `mkdocs` and `readthedocs` themes:

```yaml
plugins:
  - search
  - mike
```

### Sumi

Sumi shows a version menu in the header, and a notice on the pages of older
versions. See [Sumi's navigation docs][sumi-versions].

```yaml
theme:
  name: sumi
  version_provider: mike
plugins:
  - search
  - sumi
  - mike
```

### Material for MkDocs

```yaml
plugins:
  - search
  - mike
extra:
  version:
    provider: mike
```

See [Material's versioning docs][material-versions] for the other options,
such as the notice on older versions.

## Publishing a version

Deploy each release with its version and, for the newest one, an alias such
as `latest`:

```sh
mike deploy --push --update-aliases 1.0 latest
```

Then make `latest` the version that the root of the site opens, once:

```sh
mike set-default --push latest
```

For the next release, deploy `1.1` with the `latest` alias: the alias moves
from `1.0` to `1.1`, and the root of the site follows it.

Use the version without the patch number, `1.1` rather than `1.1.3`, so that
patch releases update their minor version in place instead of adding an entry
to the menu for every release.

Other useful commands:

*   `mike list` lists the deployed versions and their aliases.
*   `mike serve` serves the `gh-pages` branch at `http://localhost:8000/`, to
    check the version menu before pushing. Keep using `mkdocs serve` while you
    write: it shows the version you are working on, without the menu.
*   `mike delete --push 0.9` removes an old version.
*   `mike retitle --push 1.0 "1.0 (LTS)"` changes the title shown in the menu.

Without `--push`, mike only commits to your local `gh-pages` branch.

## Publishing from GitHub Actions

This workflow deploys the development docs as `dev` on every push to `main`,
and each release tag such as `v1.2.3` as `1.2` with the `latest` alias:

```yaml
name: docs
on:
  push:
    branches: [main]
    tags: ["v*"]
permissions:
  contents: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0  # mike adds a commit to the existing gh-pages branch
      - uses: actions/setup-python@v7
        with:
          python-version: "3.x"
      - run: pip install mkdocs-ng mike
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
      - if: github.ref_type == 'branch'
        run: mike deploy --push dev
      - if: github.ref_type == 'tag'
        run: |
          version="${GITHUB_REF_NAME#v}"
          mike deploy --push --update-aliases "${version%.*}" latest
```

In the repository's settings, under *Pages*, publish from the `gh-pages`
branch.

## URLs

mike adds the version to [`site_url`](configuration.md#site_url), so the
canonical URLs, the sitemap and [`llms.txt`](configuration.md#llmstxt) of
each version point to its own folder, such as
`https://example.com/1.0/guide/`.

To have search engines index only the newest docs, point the canonical URLs of
every version to the `latest` alias:

```yaml
plugins:
  - mike:
      canonical_version: latest
```

With a custom domain, keep the `CNAME` file at the root of the `gh-pages`
branch, where GitHub writes it when you set the domain in the repository's
settings, rather than in `docs_dir`: mike leaves files outside the version
folders alone.

mike makes an alias a symbolic link to its version. GitHub Pages follows it.
If your host doesn't, set `alias_type: redirect`, which writes pages that
redirect to the version instead, or `alias_type: copy`.

## Multi-language sites

On a [multi-language site](multi-language-sites.md), each version holds every
language: `1.0/` for the default language and `1.0/zh/` for Chinese. Deploy
it the same way.

NOTE: **Changed in version 1.11.2.**
Earlier versions put the language before the version in the canonical URLs,
the sitemap and the links between languages: `/zh/1.0/` instead of
`/1.0/zh/`.

For now, the version menu of mike, Sumi and Material shows on the pages of the
default language only.

[mike]: https://github.com/jimporter/mike
[ProperDocs]: https://properdocs.org/
[sumi-versions]: https://sumi.mkdocs-ng.org/docs/customize/navigation/#versions
[material-versions]: https://material.mkdocs-ng.org/setup/setting-up-versioning/

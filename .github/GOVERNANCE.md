# Governance

MkDocs NG is a community-maintained fork of MkDocs 1.x. Its job is to keep
existing MkDocs sites, plugins and themes working while the project moves
forward. This page says who maintains it, how decisions are made, and what
happens if the maintainers step away.

## Maintainers

Name | GitHub | Role | Since
--- | --- | --- | ---
Xianpeng Shen | [@shenxianpeng](https://github.com/shenxianpeng) | Lead maintainer. Owner of the `mkdocs-ng` GitHub organization, the PyPI projects and the `mkdocs-ng.org` domain. | April 2026

The same people maintain the other repositories in the
[mkdocs-ng organization](https://github.com/mkdocs-ng): the Sumi theme,
MkDocs NG Material and the plugin catalog.

MkDocs NG has one maintainer today. Finding a second one is the most important
open task for the project; see [Becoming a maintainer](#becoming-a-maintainer).

## How decisions are made

*   **Compatibility comes first.** A change that breaks an existing site, plugin
    or theme is not merged in a patch or minor release. The
    [plugin compatibility tests](https://github.com/mkdocs-ng/mkdocs/tree/main/compat)
    run on every pull request, and the
    [versioning rules](https://mkdocs-ng.org/about/release-notes/#versioning-and-support)
    say what each kind of release may change.
*   **Everyday changes**, such as bug fixes, documentation and small features,
    are merged after one maintainer approves them.
*   **Larger changes**, such as a new configuration option, a change to the
    plugin or theme API, or dropping support for something, start as an issue or
    a discussion. They stay open for comments for at least seven days before the
    pull request is merged.
*   **Disagreements** are settled by discussion. If that doesn't work, the lead
    maintainer decides. Once there are three or more maintainers, the maintainers
    decide by majority.

## Releases

Maintainers with release rights publish a release by publishing a GitHub
Release. GitHub Actions then builds the package and uploads it to PyPI with
[trusted publishing](https://docs.pypi.org/trusted-publishers/), so no
long-lived upload token exists, and PyPI keeps a signed attestation that links
each file to the workflow run that built it. Every release has
[release notes](https://mkdocs-ng.org/about/release-notes/).

Security issues are handled as the
[security policy](https://github.com/mkdocs-ng/mkdocs/security/policy) says.

## Becoming a maintainer

Maintainers are invited by the existing maintainers. There is no fixed
checklist, but the usual path is a few months of steady help: answering
issues and discussions, reviewing pull requests, and sending fixes. Rights are
given in steps: triage first, then merge rights, then release rights and
ownership of the organization and the PyPI projects.

Issues labelled
[`good first issue`](https://github.com/mkdocs-ng/mkdocs/labels/good%20first%20issue)
are a good place to start. If you would like to help maintain MkDocs NG, say so
in [Discussions](https://github.com/orgs/mkdocs-ng/discussions).

## If the maintainers step away

MkDocs 1.x stalled when its maintainers moved on to a rewrite, so MkDocs NG
plans for this:

*   **Shared ownership.** The goal is that at least two people own the GitHub
    organization, the PyPI projects and the `mkdocs-ng.org` domain. Until there
    is a second maintainer, only the lead maintainer does.
*   **Handing over.** A maintainer who wants to stop says so in a public
    discussion and passes their rights to the remaining maintainers or to a
    regular contributor.
*   **When nobody answers.** If no maintainer has responded to issues or security
    reports for 90 days, the project counts as unmaintained. The maintainers will
    not oppose a request to move the PyPI projects to an active contributor under
    [PEP 541](https://peps.python.org/pep-0541/).
*   **The code stays open.** MkDocs NG is released under the
    [BSD-2-Clause license](https://github.com/mkdocs-ng/mkdocs/blob/main/LICENSE),
    so anyone can fork it and continue.

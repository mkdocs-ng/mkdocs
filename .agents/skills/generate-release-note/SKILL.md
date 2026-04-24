---
name: generate-release-note
description: Generate and insert a user-facing release note entry for the current GitHub pull request in docs/about/release-notes.md. Use when the user asks to create a release note, changelog entry, user-facing PR summary, or to update release notes for a PR.
---

# Generate Release Note

## Overview

Generate one concise, user-facing release note entry for the current PR and insert it into the latest release section of `docs/about/release-notes.md`.

## Workflow

1. Inspect the current release note style:

   ```bash
   sed -n '1,120p' docs/about/release-notes.md
   ```

2. Gather current PR context:

   ```bash
   gh pr view --json number,title,body,url,closingIssuesReferences,files,commits
   ```

3. Draft one release note bullet in the style of the latest section. Use English by default.

4. Choose the target category:
   - `Fixed` for bug fixes and corrected user-visible behavior.
   - `Added` for new user-facing capabilities.
   - `Changed` for changed behavior, defaults, or compatibility.
   - `Maintenance` for dependencies, packaging, CI, release automation, or maintainer-facing work.
   - Prefer an existing category in the latest release section when it fits.

5. Insert the bullet:

   ```bash
   python3 .agents/skills/generate-release-note/scripts/insert_release_note.py \
     --category Fixed \
     --note '* Fix anchor link validation so strict builds fail when missing anchors are reported as warnings. #30'
   ```

6. Re-read the top of `docs/about/release-notes.md` and make sure the entry landed in the correct latest release section.

## Placement Rules

Always update `docs/about/release-notes.md`. Insert into the first `## Version ... (...)` section in the file, which is the current next-release section.

If the top section is an unreleased version such as `## Version 1.7.1 (Unreleased)`, use that section. If the next version number is already known, use that version section. Do not insert into older published versions.

When a target category already exists, append the entry at the end of that category. When it does not exist, create the category inside the latest release section before the next version heading.

## Entry Style

Match the existing release note source style:

- Use `* ` bullets.
- Write concise, user-facing English.
- Describe behavior or value users can observe.
- Avoid implementation details such as file names, commit hashes, tests, or internal refactors unless directly relevant to users.
- Use backticks for commands, options, configuration keys, package names, and code-like terms.

Examples:

```markdown
* Fix `mkdocs serve --livereload` so the option is recognized correctly again. #4
* Remove the unmaintained `mergedeep` dependency by replacing it with an internal deep-merge helper for inherited YAML configuration. #29
```

## Link Rules

If `closingIssuesReferences` has user issues, end the entry with the issue number references such as `#30`. Keep issue references short in the source file; `docs/hooks.py` rewrites them to the correct GitHub issue links during docs rendering.

If there is no user issue, end the entry with a PR Markdown link such as `#123` that points to the PR URL.

If multiple user issues are relevant, include all issue references at the end of the same bullet.

## Verification

After insertion, check:

- The entry is under the latest `## Version ... (...)` section.
- The category heading is appropriate and matches nearby release note style.
- Issue-backed entries use bare issue references.
- PR-backed entries use Markdown PR links.
- The entry is not duplicated.

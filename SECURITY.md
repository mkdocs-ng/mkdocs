# Security Policy

## Supported Versions

Only the latest released version of MkDocs-NG receives security fixes.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

To report a vulnerability, please use [GitHub Private Security Advisories](https://github.com/mkdocs-ng/mkdocs/security/advisories/new).

You can expect:
- Acknowledgement within **48 hours**
- A fix or mitigation plan within **7 days** for critical issues
- Credit in the release notes (unless you prefer to remain anonymous)

## Scope

Issues that are considered in scope:

- Remote code execution
- Arbitrary file read/write during build
- Path traversal vulnerabilities
- Template injection

Issues that are **out of scope**:

- Vulnerabilities in generated static HTML output (the user controls the content)
- Issues requiring a malicious `mkdocs.yml` authored by the site owner themselves

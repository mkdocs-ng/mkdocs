# Repository Review (2026-04-23)

Top 5 high-priority improvement recommendations identified from a quick repository audit:

1. Consolidate linting/fixing workflow definitions to avoid config drift between Hatch scripts, pre-commit hooks, and GitHub Actions.
2. Add automated dependency/security update and vulnerability scanning (Dependabot + pip-audit/OSV scan in CI).
3. Tighten release safety by restricting release tags to version patterns (for example `v*` with semantic checks) and optional manual approval gates.
4. Rebalance CI matrix strategy (smoke vs full matrix) to reduce turnaround time while preserving cross-platform confidence.
5. Retire known temporary compatibility shims/TODO paths in rendering and config handling as minimum dependency baselines advance.

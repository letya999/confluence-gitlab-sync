# Release Guide

This repository ships two artifacts from one tag:

- Python package: `confluence-sync-mcp` (PyPI)
- npm launcher: `confluence-sync-mcp-npm` (npm)

Release trigger is a Git tag `vX.Y.Z`.

## Prerequisites

1. PyPI project `confluence-sync-mcp` exists and allows GitHub OIDC trusted publishing from this repository.
2. GitHub secret `NPM_TOKEN` is configured with publish rights for `confluence-sync-mcp-npm`.
3. You have push permission for tags.

## Release Steps

1. Update Python package version in `packages/confluence-sync-mcp/pyproject.toml`.
2. Update npm package version in `packages/confluence-sync-mcp-npm/package.json`.
3. Ensure both versions are identical, e.g. `0.2.0`.
4. Run local checks:

```bash
cd packages/confluence-sync-mcp
python -m pip install -e .[dev]
pytest -q
ruff check src tests
mypy src
```

```bash
cd ../confluence-sync-mcp-npm
node --check bin/confluence-sync-mcp.js
npm pack --dry-run
```

5. Commit changes:

```bash
git add packages/confluence-sync-mcp/pyproject.toml packages/confluence-sync-mcp-npm/package.json
git commit -m "release: v0.2.0"
```

6. Create and push tag:

```bash
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

## What GitHub Actions Does

Workflow: `.github/workflows/release.yml`

1. Validates tag version (`vX.Y.Z`) matches both package versions.
2. Builds and publishes `packages/confluence-sync-mcp` to PyPI.
3. Publishes `packages/confluence-sync-mcp-npm` to npm.

If version mismatch is detected, publish jobs are blocked.

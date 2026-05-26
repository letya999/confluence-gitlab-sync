# Confluence GitLab Sync Skill

English | [Русский](README.ru.md)

Sync Markdown documentation from local folders or GitLab repositories into Confluence via MCP tools.

## What this repository contains

- `skills/confluence-gitlab-sync/SKILL.md`: skill definition and operator workflow.
- `packages/confluence-sync-mcp`: Python MCP server implementation.
- `packages/confluence-sync-mcp-npm`: npm launcher that bootstraps and runs the Python MCP server.
- `skills/confluence-gitlab-sync/references/mcp_config_template.json`: MCP client config template.
- `skills/confluence-gitlab-sync/scripts/run_server.*`: server startup wrappers.

## Install in Codex

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

## Runtime distribution options for MCP server

1. Python package runtime:
   - publish `packages/confluence-sync-mcp` to PyPI as `confluence-sync-mcp`
   - run with `python -m confluence_sync.server` or `confluence-sync-mcp`
2. npm runtime launcher:
   - publish `packages/confluence-sync-mcp-npm` to npm as `confluence-sync-mcp-npm`
   - run with `npx -y confluence-sync-mcp-npm@<version>`

## Quick start for local development

```bash
cd packages/confluence-sync-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
pytest -q
```

## Quality gates

GitHub Actions runs:
- `ruff` (lint)
- static analysis (`mypy`)
- OWASP-style dependency scan (`dependency-check`)
- tests (`pytest`)

## Open source docs

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [LICENSE](LICENSE)
- [RELEASE.md](RELEASE.md)

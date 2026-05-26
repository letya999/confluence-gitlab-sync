# Confluence GitLab Sync Skill

English | [Русский](README.ru.md)

Sync Markdown documentation from local folders or GitLab repositories into Confluence via MCP tools.

## What this repository contains

- `skills/confluence-gitlab-sync/SKILL.md`: skill definition and operator workflow.
- `packages/confluence-sync-mcp`: Python MCP server implementation.
- `skills/confluence-gitlab-sync/references/mcp_config_template.json`: MCP client config template.
- `skills/confluence-gitlab-sync/scripts/run_server.*`: server startup wrappers.

## Install in Codex

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

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

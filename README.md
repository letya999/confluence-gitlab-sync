# Confluence GitLab Sync Skill

English | [Русский](README.ru.md)

Sync Markdown documentation from local folders or GitLab repositories into Confluence via MCP tools.

## What this repository contains

- `SKILL.md`: skill definition and operator workflow.
- `tools/confluence_sync`: Python MCP server implementation.
- `references/mcp_config_template.json`: MCP client config template.
- `scripts/run_server.*`: server startup wrappers.

## Install in Codex

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

## Quick start for local development

```bash
cd tools/confluence_sync
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

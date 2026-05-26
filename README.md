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

## Install skill in CLI hosts

Use this skill path from the repo:
- `skills/confluence-gitlab-sync`

### Codex CLI

```bash
$skill-installer install https://github.com/letya999/confluence-gitlab-sync/tree/main/skills/confluence-gitlab-sync
```

Then restart Codex session.

### Claude Code CLI

1. Add the skill folder to your Claude skills directory.
2. Register MCP server using the same config from:
   - `skills/confluence-gitlab-sync/references/mcp_config_template.json`
3. Restart Claude Code CLI.

### Antigravity CLI

1. Import/install skill from:
   - `https://github.com/letya999/confluence-gitlab-sync/tree/main/skills/confluence-gitlab-sync`
2. Add MCP server entry (`command`, `args`, `env`) using the template:
   - `skills/confluence-gitlab-sync/references/mcp_config_template.json`
3. Restart Antigravity CLI.

## MCP server install and run

### Option A: npm/npx launcher

1. Publish or use package `confluence-sync-mcp-npm`.
2. Run MCP server:

```bash
npx -y confluence-sync-mcp-npm@0.1.0
```

This launcher bootstraps Python runtime and starts `confluence_sync.server`.

### Option B: Python package

```bash
cd packages/confluence-sync-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
python -m confluence_sync.server
```

If installed from package index, entrypoint is also available:

```bash
confluence-sync-mcp
```

## MCP client setup (Codex / Claude / other hosts, including Antigravity)

Use the template:
- `skills/confluence-gitlab-sync/references/mcp_config_template.json`

Minimal command variants:
- `npx -y confluence-sync-mcp-npm@0.1.0`
- `python -m confluence_sync.server`
- `powershell -File packages/confluence-sync-mcp/scripts/run_server_venv.ps1`
- `bash packages/confluence-sync-mcp/scripts/run_server_venv.sh`

Example `mcpServers` block (works for hosts that use MCP JSON config):

```json
{
  "mcpServers": {
    "confluence-gitlab-sync": {
      "command": "npx",
      "args": ["-y", "confluence-sync-mcp-npm@0.1.0"],
      "env": {
        "PYTHONUTF8": "1",
        "CONFLUENCE_BASE_URL": "https://your-org.atlassian.net/wiki",
        "CONFLUENCE_SPACE_KEY": "DOCS",
        "CONFLUENCE_PARENT_PAGE_ID": "123456789",
        "CONFLUENCE_USERNAME": "you@company.com",
        "CONFLUENCE_API_TOKEN": "<token>",
        "GITLAB_ENABLED": "true",
        "GITLAB_BASE_URL": "https://gitlab.com",
        "GITLAB_TOKEN": "<token>",
        "GITLAB_PROJECT_ID": "12345678",
        "GITLAB_REF": "main",
        "GITLAB_DOCS_PATH": "docs"
      }
    }
  }
}
```

For Claude Desktop: place the same `mcpServers` object into your local Claude MCP config file.
For Codex: use the same server block in Codex MCP config or skill runtime config.
For Antigravity/other MCP hosts: map the same `command`, `args`, and `env` fields in that host's MCP settings UI/file.

## Credentials: where to get them

### Confluence (Atlassian Cloud)

- `CONFLUENCE_BASE_URL`: your Confluence URL, usually `https://<org>.atlassian.net/wiki`.
- `CONFLUENCE_SPACE_KEY`: open target space in Confluence, copy its key from space settings/header.
- `CONFLUENCE_PARENT_PAGE_ID`: open target parent page and copy numeric page id from URL.
- `CONFLUENCE_USERNAME`: Atlassian account email.
- `CONFLUENCE_API_TOKEN`: create at Atlassian API token page (Account Settings -> Security -> API tokens).

### GitLab

- `GITLAB_BASE_URL`: `https://gitlab.com` or self-hosted URL.
- `GITLAB_TOKEN`: Personal Access Token with `read_api` (and repository read permissions if required).
- `GITLAB_PROJECT_ID`: numeric project id from GitLab project page/API.
- `GITLAB_REF`: branch/tag, usually `main`.
- `GITLAB_DOCS_PATH`: docs folder path in repo, usually `docs`.

### Security notes

- Never commit tokens to git.
- Prefer MCP host secret storage over plaintext files.
- Rotate tokens if they were exposed.

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

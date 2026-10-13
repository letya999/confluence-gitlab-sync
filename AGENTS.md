# Repository instructions

This repository maintains the `confluence-gitlab-sync` Agent Skill plus its MCP
server packages. The skill syncs Markdown documentation from local folders or
GitLab repositories into Confluence.

## Layout

- `skills/confluence-gitlab-sync/` — skill definition (`SKILL.md`), references, scripts
- `packages/confluence-sync-mcp` — Python MCP server
- `packages/confluence-sync-mcp-npm` — npm launcher

## Guardrails

- Sync targets Confluence only; never post credentials or page content to logs.
- Keep `source="local"` and `source="gitlab"` paths symmetrical; dry-run must
  stay side-effect free.
- Do not commit `.env`, tokens, Confluence/GitLab credentials, or exported dumps.
- English is the maintained language; keep `README.ru.md` in sync.

## Validation

```bash
cd packages/confluence-sync-mcp && uv run pytest
```

---
name: confluence-gitlab-sync
description: Sync Markdown documentation from local folders or GitLab repositories into Confluence via MCP tools, including dry-run planning, hierarchy creation, link validation, attachment upload, and safe apply. Use for Confluence migrations, ongoing docs sync, or GitLab-to-Confluence publishing workflows.
---

# Confluence GitLab Sync

## What this skill does

- Runs a local MCP server that syncs Markdown docs to Confluence.
- Supports `source="local"` and `source="gitlab"`.
- Preserves folder hierarchy under a target Confluence parent page.
- Resolves markdown links and uploads image/PUML attachments.

## Install (usual Codex way)

Skill definition is installed via `$skill-installer`. MCP runtime can be provided either by Python package or npm launcher.

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

After install: restart Codex.

## Runtime launcher options

- Python native:
  - `python -m confluence_sync.server`
  - or `confluence-sync-mcp` after Python package install
- npm launcher:
  - `npx -y confluence-sync-mcp-npm@<version>`
  - launcher creates venv, installs Python runtime, starts server

## MCP server runtime

Server lives at:
- `packages/confluence-sync-mcp`

Start manually from repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packages/confluence-sync-mcp/scripts/run_server_venv.ps1
```

```bash
bash packages/confluence-sync-mcp/scripts/run_server_venv.sh
```

## MCP client config

Use `skills/confluence-gitlab-sync/references/mcp_config_template.json` as parameterized template and replace placeholders.

Common launcher choices:
- `npx -y confluence-sync-mcp-npm@0.1.1`
- `python -m confluence_sync.server`
- `powershell -File packages/confluence-sync-mcp/scripts/run_server_venv.ps1`
- `bash packages/confluence-sync-mcp/scripts/run_server_venv.sh`

Credential sources:
- Confluence: Atlassian account email + API token, base URL, space key, parent page id.
- GitLab: base URL, Personal Access Token (`read_api`), project id, ref, docs path.

## Recommended operator flow

1. `smoke_check(...)`
2. `list_docs(...)` or `search_docs(...)`
3. `validate_links(...)`
4. `plan_sync(...)` and verify `collisions.count == 0`
5. `sync_to_confluence(..., dry_run=true)`
6. `sync_to_confluence(..., dry_run=false)`

## Exposed tools

- `smoke_check(...)`
- `list_docs(...)`
- `search_docs(...)`
- `validate_links(...)`
- `plan_sync(...)`
- `search_confluence_pages(...)`
- `find_semantic_confluence_match(...)`
- `suggest_markdown_match_for_page(...)`
- `suggest_confluence_match_for_markdown(...)`
- `resolve_parent_page_id(...)`
- `resolve_gitlab_project(...)`
- `sync_to_confluence(...)`
- `export_from_confluence(...)`
- `migration_operator_prompt(...)`

## Notes

- Prefer explicit `parent_page_id` for deterministic placement.
- Use `target_page_id` when you must update an exact existing Confluence page.
- If source has multiple markdown files and `target_page_id` is used, tool performs auto-match and blocks apply on low confidence, returning top candidates.
- Use `parent_title_path` with `create_missing_parent_path=true` to create missing folder pages deterministically.
- Use `selected_doc_relative_path` to explicitly choose source markdown when ambiguity is reported.
- Use `intent_text` to communicate user intent (for example, explicit rename intent).
- Use `export_from_confluence(...)` to produce markdown-only, markdown+PUML, or markdown+attachments bundles for local docs or GitLab docs folders.
- For converter behavior, edit `packages/confluence-sync-mcp/src/confluence_sync/formatter.py`.
- Bootstrap `.env` from existing local configs:

```powershell
python packages/confluence-sync-mcp/scripts/bootstrap_env_from_sources.py
```



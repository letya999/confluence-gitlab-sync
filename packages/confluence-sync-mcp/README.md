# Confluence Sync MCP

Python MCP server for syncing Markdown docs from local folders or GitLab repos into Confluence.

## Install skill

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

## npm launcher (optional runtime)

```bash
npx -y confluence-sync-mcp-npm@0.1.1
```

The launcher bootstraps a Python venv and starts `confluence_sync.server`.

## Setup

```bash
cd packages/confluence-sync-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

## Run server

```bash
cd packages/confluence-sync-mcp
confluence-sync-mcp
```

Alternative:

```bash
python -m confluence_sync.server
```

## Key capabilities

- Converts Markdown to Confluence storage format.
- Resolves `.md` links to Confluence links.
- Uploads image and PlantUML assets.
- Supports dry-run planning and safe apply.
- Supports `source=local` and `source=gitlab`.

## Common flow

1. `smoke_check(...)`
2. `plan_sync(...)`
3. `sync_to_confluence(..., dry_run=true)`
4. `sync_to_confluence(..., dry_run=false)`

## Bootstrap env

```bash
cd packages/confluence-sync-mcp
python scripts/bootstrap_env_from_sources.py --source-env /path/to/source/.env
```

Optional flags:

- `--codex-config /path/to/config.toml`
- `--out /path/to/.env`
- `--local-docs-path ./docs`

## One-shot commands

```bash
cd packages/confluence-sync-mcp
py -3 scripts/sync_once.py --source local --dry-run
py -3 scripts/sync_once.py --source local --target-page-id 997654544
py -3 scripts/export_once.py --page-id 123456 --space-key ARCH --output-dir .tmp_export --mode markdown_with_assets
```

## Test

```bash
cd packages/confluence-sync-mcp
py -3 -m pytest -q
```


# confluence-sync-mcp-npm

Node.js launcher for the `confluence-sync-mcp` Python MCP server.

## What it does

- Creates a Python virtual environment (default: `~/.confluence-sync-mcp/.venv`).
- Installs/updates the Python package.
- Starts `python -m confluence_sync.server`.

## Install

```bash
npm install -g confluence-sync-mcp-npm
```

Run:

```bash
confluence-sync-mcp
```

## Install from local clone

```bash
npm install -g ./packages/confluence-sync-mcp-npm
```

## Environment variables

- `PYTHON_BIN`: explicit Python executable to use for creating venv.
- `CONFLUENCE_SYNC_VENV_DIR`: override venv directory.
- `CONFLUENCE_SYNC_PYTHON_SPEC`: Python package spec for `pip install`.
  - default in monorepo checkout: local `packages/confluence-sync-mcp`
  - default outside monorepo: `confluence-sync-mcp` (PyPI package name)

## Typical MCP command

```json
{
  "command": "npx",
  "args": ["-y", "confluence-sync-mcp-npm@0.1.1"]
}
```

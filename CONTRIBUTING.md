# Contributing

## Scope

This skill publishes Markdown documentation (local or GitLab) into Confluence via MCP tools.

## Prerequisites

- Python 3.11+
- Access to target Confluence space
- Optional: GitLab token/project for `source=gitlab`

## Local Development

```bash
cd skills/confluence-gitlab-sync/tools/confluence_sync
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

## Tests

```bash
cd skills/confluence-gitlab-sync/tools/confluence_sync
pytest -q
```

## Style

- Keep env var names consistent with `src/confluence_sync/config.py`.
- Prefer backwards-compatible changes in MCP tool signatures.
- Update `SKILL.md` and `tools/confluence_sync/README.md` when behavior changes.

## Pull Requests

- Include a clear problem statement and change summary.
- Add or update tests for behavior changes.
- Avoid committing secrets (`.env`, tokens, private URLs).
- Use trunk-based flow: short-lived branches, frequent merges to `main`/`master`.
- Prefer Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `ci:`).

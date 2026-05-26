# Скилл Confluence GitLab Sync

[English](README.md) | Русский

Синхронизирует Markdown-документацию из локальных папок или GitLab-репозиториев в Confluence через MCP-инструменты.

## Что в репозитории

- `skills/confluence-gitlab-sync/SKILL.md`: описание скилла и рабочий сценарий оператора.
- `packages/confluence-sync-mcp`: Python-реализация MCP-сервера.
- `skills/confluence-gitlab-sync/references/mcp_config_template.json`: шаблон конфигурации MCP-клиента.
- `skills/confluence-gitlab-sync/scripts/run_server.*`: скрипты запуска сервера.

## Установка в Codex

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

## Быстрый локальный старт

```bash
cd packages/confluence-sync-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
pytest -q
```

## Проверки качества

В GitHub Actions запускаются:
- `ruff` (lint)
- статический анализ (`mypy`)
- OWASP-проверка зависимостей (`dependency-check`)
- тесты (`pytest`)

## Документы open source

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [LICENSE](LICENSE)

# Скилл Confluence GitLab Sync

[English](README.md) | Русский

Синхронизирует Markdown-документацию из локальных папок или GitLab-репозиториев в Confluence через MCP-инструменты.

## Что в репозитории

- `SKILL.md`: описание скилла и рабочий сценарий оператора.
- `tools/confluence_sync`: Python-реализация MCP-сервера.
- `references/mcp_config_template.json`: шаблон конфигурации MCP-клиента.
- `scripts/run_server.*`: скрипты запуска сервера.

## Установка в Codex

```text
$skill-installer install https://github.com/<org>/<repo>/tree/<ref>/skills/confluence-gitlab-sync
```

## Быстрый локальный старт

```bash
cd tools/confluence_sync
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

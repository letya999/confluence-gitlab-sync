from __future__ import annotations

from confluence_sync.config import build_runtime_config


def test_build_runtime_config_overrides(monkeypatch) -> None:
    monkeypatch.setenv("CONFLUENCE_BASE_URL", "https://example.atlassian.net/wiki")
    monkeypatch.setenv("CONFLUENCE_SPACE_KEY", "ENG")
    monkeypatch.setenv("CONFLUENCE_USERNAME", "u@example.com")
    monkeypatch.setenv("CONFLUENCE_API_TOKEN", "token")
    monkeypatch.setenv("LOCAL_DOCS_PATH", "./docs")
    monkeypatch.setenv("GITLAB_ENABLED", "true")
    monkeypatch.setenv("GITLAB_BASE_URL", "https://gitlab.com")
    monkeypatch.setenv("GITLAB_PROJECT_ID", "group/proj")
    monkeypatch.setenv("GITLAB_TOKEN", "gl-token")
    monkeypatch.setenv("GITLAB_REF", "main")
    monkeypatch.setenv("GITLAB_DOCS_PATH", "docs")

    cfg = build_runtime_config(
        space_key="ARCH",
        parent_page_id="123",
        local_docs_path=".",
        gitlab_project_id="group/new-proj",
        gitlab_ref="develop",
        gitlab_docs_path="architecture",
    )
    assert cfg.confluence.space_key == "ARCH"
    assert cfg.confluence.parent_page_id == "123"
    assert cfg.gitlab is not None
    assert cfg.gitlab.project_id == "group/new-proj"
    assert cfg.gitlab.ref == "develop"
    assert cfg.gitlab.docs_path == "architecture"


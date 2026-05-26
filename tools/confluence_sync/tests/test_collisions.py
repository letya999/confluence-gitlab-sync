from __future__ import annotations

from pathlib import Path

from confluence_sync.config import AppConfig, ConfluenceConfig
from confluence_sync.sync_service import detect_target_collisions


def test_detect_target_collisions(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    (docs_root / "a").mkdir(parents=True, exist_ok=True)
    (docs_root / "a" / "my-doc.md").write_text("# A", encoding="utf-8")
    (docs_root / "a" / "my_doc.md").write_text("# B", encoding="utf-8")

    cfg = AppConfig(
        confluence=ConfluenceConfig(
            base_url="https://example.atlassian.net/wiki",
            space_key="ENG",
            parent_page_id=None,
            username="u@example.com",
            api_token="token",
        ),
        local_docs_path=docs_root,
        gitlab=None,
    )

    collisions = detect_target_collisions(cfg, source="local")
    assert collisions["count"] == 1


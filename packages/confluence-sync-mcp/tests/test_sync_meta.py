from confluence_sync.sync_meta import (
    build_confluence_sync_storage_block,
    build_markdown_sync_block,
    upsert_markdown_sync_block,
)


def test_upsert_markdown_sync_block_inserts_and_updates() -> None:
    src = "# Title\n\nBody\n"
    block = build_markdown_sync_block(page_id="1", page_url="https://x", space_key="ARCH")
    out = upsert_markdown_sync_block(src, block)
    assert "confluence_page_id: 1" in out
    block2 = build_markdown_sync_block(page_id="2", page_url="https://y", space_key="ARCH")
    out2 = upsert_markdown_sync_block(out, block2)
    assert "confluence_page_id: 2" in out2
    assert "confluence_page_id: 1" not in out2


def test_build_confluence_sync_storage_block_contains_source_fields() -> None:
    block = build_confluence_sync_storage_block(
        source_type="local",
        source_root="/repo/docs",
        source_relative_path="INFRA_NATS_Registry.md",
        source_project="",
        source_ref="",
        last_synced_at="2026-05-26T10:00:00+00:00",
    )
    assert "source_type" in block
    assert "local" in block
    assert "source_root" in block
    assert "/repo/docs" in block
    assert "source_markdown_file" in block
    assert "INFRA_NATS_Registry.md" in block

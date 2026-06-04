from confluence_sync.sync_meta import (
    CONTENT_PROPERTY_KEY,
    build_confluence_sync_property_value,
    build_confluence_sync_storage_block,
    upsert_confluence_sync_storage_block,
)


def test_upsert_confluence_sync_storage_block_replaces_existing_block() -> None:
    original = (
        "<h1>Title</h1>\n"
        "<!-- sync-meta:start -->\n"
        '<ac:structured-macro ac:name="info"><ac:rich-text-body><p><strong>Sync metadata</strong></p>'
        "<table><tbody><tr><td>source_type</td><td>old</td></tr></tbody></table>"
        "</ac:rich-text-body></ac:structured-macro>\n"
        "<!-- sync-meta:end -->"
    )
    replacement = build_confluence_sync_storage_block(
        source_type="local",
        source_root="docs",
        source_relative_path="SERVICE_Metadata.md",
        last_synced_at="2026-06-04T16:00:00+00:00",
    )
    merged = upsert_confluence_sync_storage_block(original, replacement)
    assert merged.count("<!-- sync-meta:start -->") == 1
    assert "<td>local</td>" in merged
    assert "<td>old</td>" not in merged


def test_upsert_confluence_sync_storage_block_replaces_existing_block_with_windows_path() -> None:
    original = (
        "<h1>Title</h1>\n"
        "<!-- sync-meta:start -->\n"
        '<ac:structured-macro ac:name="info"><ac:rich-text-body><p><strong>Sync metadata</strong></p>'
        "<table><tbody><tr><td>source_root</td><td>old</td></tr></tbody></table>"
        "</ac:rich-text-body></ac:structured-macro>\n"
        "<!-- sync-meta:end -->"
    )
    replacement = build_confluence_sync_storage_block(
        source_type="local",
        source_root=r"C:\Users\User\docs",
        source_relative_path="SERVICE_Metadata.md",
        last_synced_at="2026-06-04T16:00:00+00:00",
    )
    merged = upsert_confluence_sync_storage_block(original, replacement)
    assert r"C:\Users\User\docs" in merged


def test_upsert_confluence_sync_storage_block_replaces_legacy_footer() -> None:
    original = (
        "<h1>Title</h1>\n"
        '<ac:structured-macro ac:name="info"><ac:rich-text-body><p><strong>Sync metadata</strong></p>'
        "<table><tbody><tr><td>source_type</td><td>old</td></tr></tbody></table>"
        "</ac:rich-text-body></ac:structured-macro>"
    )
    replacement = build_confluence_sync_storage_block(
        source_type="gitlab",
        source_root="docs",
        source_relative_path="SERVICE_Metadata.md",
        source_project="group/project",
        source_ref="main",
        last_synced_at="2026-06-04T16:00:00+00:00",
    )
    merged = upsert_confluence_sync_storage_block(original, replacement)
    assert merged.count("Sync metadata") == 1
    assert "<td>gitlab</td>" in merged


def test_build_confluence_sync_property_value_contains_expected_keys() -> None:
    payload = build_confluence_sync_property_value(
        source_type="local",
        source_root="C:/docs",
        source_relative_path="SERVICE_Metadata.md",
        space_key="ARCH",
        confluence_page_id="123",
        confluence_page_url="https://example.atlassian.net/wiki/spaces/ARCH/pages/123/Test",
        last_synced_at="2026-06-04T16:00:00+00:00",
    )
    assert CONTENT_PROPERTY_KEY == "confluence-sync-meta"
    assert payload["source_type"] == "local"
    assert payload["confluence_space_key"] == "ARCH"
    assert payload["confluence_page_id"] == "123"

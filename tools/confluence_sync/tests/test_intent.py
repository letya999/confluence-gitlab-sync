from confluence_sync.intent import extract_sync_meta_field, wants_rename


def test_extract_sync_meta_field() -> None:
    md = (
        "<!-- sync-meta:start -->\n"
        "confluence_title: Обзор системы MQOS\n"
        "<!-- sync-meta:end -->\n"
        "# Title\n"
    )
    assert extract_sync_meta_field(md, "confluence_title") == "Обзор системы MQOS"


def test_wants_rename_by_user_intent() -> None:
    assert wants_rename(
        user_intent_text="переименуй страницу в новый заголовок",
        markdown_text="# x",
        current_page_title="Old",
    )


def test_wants_rename_by_sync_meta_title_change() -> None:
    md = (
        "<!-- sync-meta:start -->\n"
        "confluence_title: New Title\n"
        "<!-- sync-meta:end -->\n"
        "# x\n"
    )
    assert wants_rename(user_intent_text="", markdown_text=md, current_page_title="Old Title")

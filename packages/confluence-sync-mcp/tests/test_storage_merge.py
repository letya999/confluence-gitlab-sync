from confluence_sync.storage_merge import merge_storage_preserving_style


def test_storage_merge_replaces_shared_sections() -> None:
    old = "<h1>Title</h1><p>Old A</p><h2>Section</h2><p>Old B</p><ac:structured-macro ac:name='note'/>"
    new = "<h1>Title</h1><p>New A</p><h2>Section</h2><p>New B</p>"
    result = merge_storage_preserving_style(old, new)
    assert result.mode == "section_patch"
    assert "New A" in result.storage_html
    assert "New B" in result.storage_html
    assert result.risk_score >= 0.0

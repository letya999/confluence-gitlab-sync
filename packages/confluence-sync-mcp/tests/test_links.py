from confluence_sync.content_processing import resolve_relative_markdown_path


def test_resolve_relative_markdown_path() -> None:
    src = "adr/sub/spec.md"
    target = "../common/overview.md"
    assert resolve_relative_markdown_path(src, target) == "adr/common/overview.md"


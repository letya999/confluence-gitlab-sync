from confluence_sync.confluence_client import ConfluenceClient


def test_section_titles_from_relative_path() -> None:
    rel = "adr/etl-jobs/my_spec.md"
    titles = ConfluenceClient.section_titles_from_relative_path(rel)
    assert titles == ["Adr", "Etl Jobs"]


def test_section_titles_from_windows_path() -> None:
    rel = r"ops\watermark_flow\runbook.md"
    titles = ConfluenceClient.section_titles_from_relative_path(rel)
    assert titles == ["Ops", "Watermark Flow"]


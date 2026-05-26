from confluence_sync.config import ConfluenceConfig
from confluence_sync.content_processing import prepare_markdown_for_confluence
from confluence_sync.models import SourceDocument


def test_inline_code_puml_gets_processed(monkeypatch) -> None:
    doc = SourceDocument(
        title="T",
        body="See `diagram.puml`",
        source="local",
        path="x.md",
        relative_path="x.md",
    )
    cfg = ConfluenceConfig(
        base_url="https://example.atlassian.net/wiki",
        space_key="ARCH",
        parent_page_id=None,
        username="u",
        api_token="t",
    )

    monkeypatch.setattr("confluence_sync.content_processing.render_puml_to_svg", lambda s: b"<svg/>")

    def read_asset(_doc, link):
        if link == "diagram.puml":
            return b"@startuml\nAlice->Bob: Hi\n@enduml"
        return None

    def upload(_page_id, filename, _content):
        return {"filename": filename, "download_url": f"https://x/{filename}"}

    storage, uploads = prepare_markdown_for_confluence(
        doc=doc,
        page_id="1",
        page_url_by_doc_path={},
        read_binary_asset=read_asset,
        upload_attachment=upload,
        confluence_cfg=cfg,
    )
    assert "https://x/diagram.svg" in storage
    assert uploads

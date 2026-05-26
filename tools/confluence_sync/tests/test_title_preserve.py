from confluence_sync.config import ConfluenceConfig
from confluence_sync.confluence_client import ConfluenceClient


def test_update_page_by_id_preserves_existing_title(monkeypatch) -> None:
    cfg = ConfluenceConfig(
        base_url="https://example.atlassian.net/wiki",
        space_key="ARCH",
        parent_page_id=None,
        username="u",
        api_token="t",
    )
    client = ConfluenceClient(cfg)

    monkeypatch.setattr(
        client,
        "get_page_by_id",
        lambda page_id, expand="": {"id": page_id, "title": "Existing", "version": {"number": 1}},
    )
    captured = {}

    def fake_update(page, title, storage_value):
        captured["title"] = title
        return type("R", (), {"title": title, "page_id": page["id"], "action": "updated", "url": "u"})()

    monkeypatch.setattr(client, "update_page", fake_update)
    client.update_page_by_id("1", title="New", storage_value="<p>x</p>", preserve_existing_title=True)
    assert captured["title"] == "Existing"

from confluence_sync.config import AppConfig, ConfluenceConfig
from confluence_sync.confluence_client import ConfluenceClient, MermaidExtension
from confluence_sync.sync_service import _resolve_mermaid_config


def test_extract_mermaid_extension_from_adf_storage() -> None:
    storage = (
        "<ac:adf-extension><ac:adf-node type=\"extension\">"
        "<ac:adf-attribute key=\"extension-key\">ext/key</ac:adf-attribute>"
        "<ac:adf-attribute key=\"parameters\">"
        "<ac:adf-parameter key=\"extension-id\">ari:cloud:ecosystem::extension/ext/key</ac:adf-parameter>"
        "<ac:adf-parameter key=\"extension-title\">Mermaid Diagram</ac:adf-parameter>"
        "<ac:adf-parameter key=\"guest-params\">"
        "<ac:adf-parameter key=\"diagram-source\">flowchart LR\nA-->B</ac:adf-parameter>"
        "</ac:adf-parameter>"
        "</ac:adf-attribute>"
        "</ac:adf-node></ac:adf-extension>"
    )
    discovered = ConfluenceClient._extract_mermaid_extension(storage)
    assert discovered == MermaidExtension(
        extension_key="ext/key",
        extension_id="ari:cloud:ecosystem::extension/ext/key",
        extension_title="Mermaid Diagram",
    )


def test_resolve_mermaid_config_uses_discovered_extension(monkeypatch) -> None:
    cfg = AppConfig(
        confluence=ConfluenceConfig(
            base_url="https://example.atlassian.net/wiki",
            space_key="ARCH",
            parent_page_id=None,
            username="u",
            api_token="t",
            mermaid_mode="auto",
        ),
        local_docs_path="C:/docs",  # type: ignore[arg-type]
        gitlab=None,
    )
    client = ConfluenceClient(cfg.confluence)
    monkeypatch.setattr(
        client,
        "discover_mermaid_extension",
        lambda: MermaidExtension(
            extension_key="ext/key",
            extension_id="ari:cloud:ecosystem::extension/ext/key",
            extension_title="Mermaid Diagram",
        ),
    )

    resolved = _resolve_mermaid_config(client, cfg)
    assert resolved.confluence.mermaid_mode == "forge_extension"
    assert resolved.confluence.mermaid_extension_key == "ext/key"
    assert resolved.confluence.mermaid_extension_id == "ari:cloud:ecosystem::extension/ext/key"


def test_resolve_mermaid_config_keeps_explicit_macro_mode() -> None:
    cfg = AppConfig(
        confluence=ConfluenceConfig(
            base_url="https://example.atlassian.net/wiki",
            space_key="ARCH",
            parent_page_id=None,
            username="u",
            api_token="t",
            mermaid_mode="macro",
        ),
        local_docs_path="C:/docs",  # type: ignore[arg-type]
        gitlab=None,
    )
    client = ConfluenceClient(cfg.confluence)
    resolved = _resolve_mermaid_config(client, cfg)
    assert resolved == cfg

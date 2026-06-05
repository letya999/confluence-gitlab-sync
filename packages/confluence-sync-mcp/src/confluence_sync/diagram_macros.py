from __future__ import annotations

import base64
import uuid
import zlib
from html import escape
from urllib.parse import quote, unquote

from .config import ConfluenceConfig


def _cdata(text: str) -> str:
    return text.replace("]]>", "]]]]><![CDATA[>")


def normalize_diagram_newlines(text: str) -> str:
    # Be tolerant to PowerShell-style escaped literals accidentally persisted to files.
    normalized = text.replace("`r`n", "\n").replace("`n", "\n").replace("`r", "\n")
    return normalized.replace("\r\n", "\n").replace("\r", "\n")


def encode_plantumlcloud_data(diagram_source: str) -> str:
    encoded_uri = quote(normalize_diagram_newlines(diagram_source), safe="")
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed_raw = compressor.compress(encoded_uri.encode("utf-8")) + compressor.flush()
    return base64.b64encode(compressed_raw).decode("ascii")


def decode_plantumlcloud_data(encoded: str) -> str:
    raw = base64.b64decode(encoded)
    text = zlib.decompress(raw, wbits=-15).decode("utf-8", errors="replace")
    return normalize_diagram_newlines(unquote(text))


def build_plantuml_macro(filename: str, puml_source: str, cfg: ConfluenceConfig) -> str:
    data = encode_plantumlcloud_data(puml_source)
    macro_name = cfg.plantuml_macro_name or "plantumlcloud"
    return (
        f'<ac:structured-macro ac:name="{escape(macro_name)}" ac:schema-version="1" data-layout="default">'
        f"<ac:parameter ac:name=\"toolbar\">bottom</ac:parameter>"
        f"<ac:parameter ac:name=\"filename\">{escape(filename)}</ac:parameter>"
        f"<ac:parameter ac:name=\"data\">{escape(data)}</ac:parameter>"
        f"<ac:parameter ac:name=\"compressed\">true</ac:parameter>"
        f"<ac:parameter ac:name=\"revision\">1</ac:parameter>"
        f"</ac:structured-macro>"
    )


def build_mermaid_macro(diagram_source: str, cfg: ConfluenceConfig) -> str:
    diagram_source = normalize_diagram_newlines(diagram_source)
    mode = (cfg.mermaid_mode or "svg").strip().lower()
    if mode == "auto":
        mode = "forge_extension" if cfg.mermaid_extension_key.strip() and cfg.mermaid_extension_id.strip() else "macro"
    if mode == "macro":
        macro_name = cfg.mermaid_macro_name or "mermaid-cloud"
        return (
            f'<ac:structured-macro ac:name="{escape(macro_name)}" ac:schema-version="1" data-layout="default">'
            f"<ac:plain-text-body><![CDATA[{_cdata(diagram_source)}]]></ac:plain-text-body>"
            f"</ac:structured-macro>"
        )

    if mode == "forge_extension":
        extension_key = cfg.mermaid_extension_key.strip()
        extension_id = cfg.mermaid_extension_id.strip()
        if not extension_key or not extension_id:
            raise ValueError(
                "CONFLUENCE_MERMAID_MODE=forge_extension requires CONFLUENCE_MERMAID_EXTENSION_KEY "
                "and CONFLUENCE_MERMAID_EXTENSION_ID"
            )
        local_id = str(uuid.uuid4())
        title = escape(cfg.mermaid_extension_title or "Mermaid Diagram")
        return (
            "<ac:adf-extension>"
            "<ac:adf-node type=\"extension\">"
            f"<ac:adf-attribute key=\"extension-key\">{escape(extension_key)}</ac:adf-attribute>"
            "<ac:adf-attribute key=\"extension-type\">com.atlassian.ecosystem</ac:adf-attribute>"
            "<ac:adf-attribute key=\"parameters\">"
            f"<ac:adf-parameter key=\"local-id\">{local_id}</ac:adf-parameter>"
            f"<ac:adf-parameter key=\"extension-id\">{escape(extension_id)}</ac:adf-parameter>"
            f"<ac:adf-parameter key=\"extension-title\">{title}</ac:adf-parameter>"
            "<ac:adf-parameter key=\"layout\">extension</ac:adf-parameter>"
            "<ac:adf-parameter key=\"guest-params\">"
            f"<ac:adf-parameter key=\"diagram-source\">{escape(diagram_source)}</ac:adf-parameter>"
            "</ac:adf-parameter>"
            "</ac:adf-attribute>"
            f"<ac:adf-attribute key=\"text\">{title}</ac:adf-attribute>"
            "<ac:adf-attribute key=\"layout\">default</ac:adf-attribute>"
            f"<ac:adf-attribute key=\"local-id\">{local_id}</ac:adf-attribute>"
            "</ac:adf-node>"
            "</ac:adf-extension>"
        )
    raise ValueError(f"Unsupported mermaid mode: {cfg.mermaid_mode}")

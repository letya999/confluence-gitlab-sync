from __future__ import annotations

import posixpath
import re
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

import requests

from .config import ConfluenceConfig
from .diagram_macros import build_mermaid_macro, build_plantuml_macro
from .formatter import markdown_to_confluence_storage
from .models import SourceDocument

_MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
_IMG_LINK_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_MERMAID_FENCE_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", flags=re.DOTALL | re.IGNORECASE)
_INLINE_PUML_RE = re.compile(r"`([^`\n]+\.puml)`", flags=re.IGNORECASE)
_PLAIN_PUML_RE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_\-./\\]+\.puml)(?![\w/.-])", flags=re.IGNORECASE)


def _normalize_path(path_value: str) -> str:
    return path_value.replace("\\", "/")


def resolve_relative_markdown_path(doc_relative_path: str, target_link: str) -> str:
    normalized_doc = _normalize_path(doc_relative_path)
    normalized_link = _normalize_path(target_link)
    base_dir = posixpath.dirname(normalized_doc)
    joined = posixpath.normpath(posixpath.join(base_dir, normalized_link))
    return joined


def render_puml_to_svg(puml_source: str, kroki_url: str = "https://kroki.io") -> bytes:
    endpoint = f"{kroki_url.rstrip('/')}/plantuml/svg"
    resp = requests.post(endpoint, data=puml_source.encode("utf-8"), timeout=120)
    resp.raise_for_status()
    return resp.content


def render_mermaid_to_svg(mermaid_source: str, kroki_url: str = "https://kroki.io") -> bytes:
    endpoint = f"{kroki_url.rstrip('/')}/mermaid/svg"
    resp = requests.post(endpoint, data=mermaid_source.encode("utf-8"), timeout=120)
    resp.raise_for_status()
    return resp.content


def _default_asset_name(link: str, fallback_suffix: str = "") -> str:
    name = Path(_normalize_path(link)).name
    if name:
        return name
    return f"asset{fallback_suffix}"


def prepare_markdown_for_confluence(
    doc: SourceDocument,
    page_id: str,
    page_url_by_doc_path: dict[str, str],
    read_binary_asset: Callable[[SourceDocument, str], bytes | None],
    upload_attachment: Callable[[str, str, bytes], dict[str, str]],
    confluence_cfg: ConfluenceConfig,
) -> tuple[str, list[dict[str, str]]]:
    text = doc.body
    uploads: list[dict[str, str]] = []
    raw_block_by_token: dict[str, str] = {}

    def reserve_raw_block(raw: str) -> str:
        token = f"CONFLUENCE_RAW_BLOCK_{uuid4().hex}"
        raw_block_by_token[token] = raw
        return f"\n\n{token}\n\n"

    def replace_mermaid_fence(match: re.Match[str]) -> str:
        source = match.group(1).strip()
        mode = (confluence_cfg.mermaid_mode or "svg").strip().lower()
        if mode == "svg":
            svg_bytes = render_mermaid_to_svg(source)
            filename = f"mermaid_{uuid4().hex[:8]}.svg"
            uploaded = upload_attachment(page_id, filename, svg_bytes)
            uploads.append(uploaded)
            if uploaded.get("download_url"):
                return f"![mermaid]({uploaded['download_url']})"
            return match.group(0)
        macro = build_mermaid_macro(source, confluence_cfg)
        return reserve_raw_block(macro)

    text = _MERMAID_FENCE_RE.sub(replace_mermaid_fence, text)

    def _puml_markup(label: str, link: str) -> str:
        puml_bytes = read_binary_asset(doc, link)
        if not puml_bytes:
            return f"`{link}`"
        resolved = resolve_relative_markdown_path(doc.relative_path, link)
        puml_source = puml_bytes.decode("utf-8", errors="ignore")
        if (confluence_cfg.plantuml_mode or "svg").strip().lower() == "macro":
            macro = build_plantuml_macro(f"{Path(resolved).stem}.svg", puml_source, confluence_cfg)
            return reserve_raw_block(macro)
        svg_bytes = render_puml_to_svg(puml_source)
        filename = f"{Path(resolved).stem}.svg"
        uploaded = upload_attachment(page_id, filename, svg_bytes)
        uploads.append(uploaded)
        if uploaded.get("download_url"):
            return f"![{label}]({uploaded['download_url']})"
        return f"`{link}`"

    def replace_inline_puml(match: re.Match[str]) -> str:
        link = match.group(1).strip()
        return _puml_markup(Path(link).stem, link)

    text = _INLINE_PUML_RE.sub(replace_inline_puml, text)

    # Best-effort plain text conversion for lines like "see x.puml"
    def replace_plain_puml(match: re.Match[str]) -> str:
        link = match.group(1).strip()
        return _puml_markup(Path(link).stem, link)

    text = _PLAIN_PUML_RE.sub(replace_plain_puml, text)

    def replace_md_link(match: re.Match[str]) -> str:
        label, link = match.group(1), match.group(2).strip()
        if link.startswith(("http://", "https://", "#")):
            return match.group(0)
        if link.lower().endswith(".puml"):
            return _puml_markup(label, link)
        if link.lower().endswith(".md"):
            resolved = resolve_relative_markdown_path(doc.relative_path, link)
            target_url = page_url_by_doc_path.get(resolved)
            if target_url:
                return f"[{label}]({target_url})"
        return match.group(0)

    text = _MD_LINK_RE.sub(replace_md_link, text)

    def replace_image_or_puml(match: re.Match[str]) -> str:
        alt, link = match.group(1), match.group(2).strip()
        if link.startswith(("http://", "https://")):
            return match.group(0)

        resolved = resolve_relative_markdown_path(doc.relative_path, link)
        if link.lower().endswith(".puml") or resolved.lower().endswith(".puml"):
            return _puml_markup(alt or Path(link).stem, link)

        asset_bytes = read_binary_asset(doc, link)
        if not asset_bytes:
            return match.group(0)
        filename = _default_asset_name(link)
        uploaded = upload_attachment(page_id, filename, asset_bytes)
        uploads.append(uploaded)
        if uploaded.get("download_url"):
            return f"![{alt}]({uploaded['download_url']})"
        return match.group(0)

    text = _IMG_LINK_RE.sub(replace_image_or_puml, text)
    storage_html = markdown_to_confluence_storage(text)
    for token, raw in raw_block_by_token.items():
        storage_html = storage_html.replace(f"<p>{token}</p>", raw).replace(token, raw)
    return storage_html, uploads


def extract_markdown_links(markdown_text: str) -> list[str]:
    return [m.group(2).strip() for m in _MD_LINK_RE.finditer(markdown_text)]


def extract_image_links(markdown_text: str) -> list[str]:
    return [m.group(2).strip() for m in _IMG_LINK_RE.finditer(markdown_text)]


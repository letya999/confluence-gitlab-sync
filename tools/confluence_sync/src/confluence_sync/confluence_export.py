from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re
from typing import Any

from .confluence_client import ConfluenceClient
from .diagram_macros import decode_plantumlcloud_data


@dataclass(frozen=True)
class ExportOptions:
    include_attachments: bool = True
    extract_mermaid: bool = True
    extract_plantuml: bool = True
    output_mode: str = "single_markdown"  # single_markdown | markdown_with_assets | markdown_for_gitlab_docs


_TAG_RE = re.compile(r"<[^>]+>")
_MERMAID_ADF_RE = re.compile(
    r"<ac:adf-extension>.*?<ac:adf-parameter key=\"diagram-source\">(.*?)</ac:adf-parameter>.*?</ac:adf-extension>",
    flags=re.DOTALL,
)
_PLANTUML_RE = re.compile(
    r"<ac:structured-macro[^>]*ac:name=\"plantumlcloud\"[^>]*>.*?<ac:parameter ac:name=\"data\">(.*?)</ac:parameter>.*?</ac:structured-macro>",
    flags=re.DOTALL,
)
_AC_IMAGE_ATTACHMENT_RE = re.compile(
    r"<ac:image[^>]*>.*?<ri:attachment[^>]*ri:filename=\"([^\"]+)\"[^>]*/>.*?</ac:image>",
    flags=re.DOTALL,
)


def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text)


def _storage_to_markdown_baseline(storage: str) -> str:
    out = storage
    out = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1>", lambda m: f"\n{'#' * int(m.group(1))} {unescape(_strip_tags(m.group(2)).strip())}\n", out, flags=re.DOTALL)
    out = re.sub(r"<p[^>]*>(.*?)</p>", lambda m: f"\n{unescape(_strip_tags(m.group(1)).strip())}\n", out, flags=re.DOTALL)
    out = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: f"- {unescape(_strip_tags(m.group(1)).strip())}\n", out, flags=re.DOTALL)
    out = re.sub(r"<br\\s*/?>", "\n", out)
    out = re.sub(r"<hr[^>]*>", "\n---\n", out)
    out = re.sub(r"</?(ul|ol|table|tbody|tr|td|th|colgroup|col)[^>]*>", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", _strip_tags(out))
    return unescape(out).strip() + "\n"


def _replace_mermaid(storage: str) -> tuple[str, list[str]]:
    diagrams: list[str] = []

    def repl(match: re.Match[str]) -> str:
        source = unescape(match.group(1)).strip()
        diagrams.append(source)
        return f"\n```mermaid\n{source}\n```\n"

    return _MERMAID_ADF_RE.sub(repl, storage), diagrams


def _replace_plantuml(storage: str) -> tuple[str, list[str]]:
    puml_list: list[str] = []

    def repl(match: re.Match[str]) -> str:
        data = match.group(1).strip()
        source = decode_plantumlcloud_data(data)
        idx = len(puml_list) + 1
        filename = f"diagram_{idx:02d}.puml"
        puml_list.append(source)
        return f"\n![PlantUML {idx}]({filename})\n"

    return _PLANTUML_RE.sub(repl, storage), puml_list


def _replace_images(storage: str) -> tuple[str, list[str]]:
    names: list[str] = []

    def repl(match: re.Match[str]) -> str:
        filename = match.group(1).strip()
        names.append(filename)
        return f"\n![{filename}]({filename})\n"

    return _AC_IMAGE_ATTACHMENT_RE.sub(repl, storage), names


def export_confluence_page(
    client: ConfluenceClient,
    *,
    page_id: str,
    output_dir: Path,
    options: ExportOptions,
) -> dict[str, Any]:
    page = client.get_page_by_id(page_id, expand="title,body.storage,_links,version")
    title = str(page.get("title", f"page_{page_id}"))
    storage = str(page.get("body", {}).get("storage", {}).get("value", ""))
    safe_title = re.sub(r"[^a-zA-Z0-9_\\-]+", "_", title).strip("_") or f"page_{page_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    edited = storage
    mermaid_diagrams: list[str] = []
    puml_diagrams: list[str] = []
    image_refs: list[str] = []

    if options.extract_mermaid:
        edited, mermaid_diagrams = _replace_mermaid(edited)
    if options.extract_plantuml:
        edited, puml_diagrams = _replace_plantuml(edited)
    edited, image_refs = _replace_images(edited)
    markdown = _storage_to_markdown_baseline(edited)

    md_path = output_dir / f"{safe_title}.md"
    md_path.write_text(markdown, encoding="utf-8")

    written_puml: list[str] = []
    for i, source in enumerate(puml_diagrams, start=1):
        filename = f"diagram_{i:02d}.puml"
        (output_dir / filename).write_text(source, encoding="utf-8")
        written_puml.append(filename)

    downloaded: list[str] = []
    if options.include_attachments and options.output_mode != "single_markdown":
        all_attachments = client.list_attachments(page_id)
        wanted = set(image_refs) if image_refs else {a["title"] for a in all_attachments}
        for att in all_attachments:
            name = att["title"]
            url = att["download_url"]
            if name not in wanted or not url:
                continue
            data = client.download_attachment(url)
            (output_dir / name).write_bytes(data)
            downloaded.append(name)

    return {
        "page_id": page_id,
        "title": title,
        "url": f"{client.base}{page.get('_links', {}).get('webui', '')}",
        "version": page.get("version", {}).get("number"),
        "markdown_file": str(md_path),
        "puml_files": written_puml,
        "attachments_downloaded": downloaded,
        "mermaid_count": len(mermaid_diagrams),
        "plantuml_count": len(puml_diagrams),
    }

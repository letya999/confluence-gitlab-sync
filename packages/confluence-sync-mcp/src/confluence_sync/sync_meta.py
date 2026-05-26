from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

_START = "<!-- sync-meta:start -->"
_END = "<!-- sync-meta:end -->"


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_markdown_sync_block(
    *,
    page_id: str,
    page_url: str,
    space_key: str,
    confluence_updated_at: str = "",
    last_synced_at: str = "",
) -> str:
    sync_at = last_synced_at or _iso_now()
    return (
        f"{_START}\n"
        f"confluence_page_id: {page_id}\n"
        f"confluence_url: {page_url}\n"
        f"confluence_space_key: {space_key}\n"
        f"confluence_last_updated_at: {confluence_updated_at}\n"
        f"last_synced_at: {sync_at}\n"
        f"{_END}\n\n"
    )


def upsert_markdown_sync_block(markdown_text: str, block: str) -> str:
    start = markdown_text.find(_START)
    end = markdown_text.find(_END)
    if start >= 0 and end > start:
        end += len(_END)
        tail = markdown_text[end:]
        if tail.startswith("\n"):
            return markdown_text[:start] + block + tail[1:]
        return markdown_text[:start] + block + tail
    return block + markdown_text


def write_markdown_sync_block(path: str | Path, block: str) -> None:
    p = Path(path)
    src = p.read_text(encoding="utf-8")
    out = upsert_markdown_sync_block(src, block)
    if out != src:
        p.write_text(out, encoding="utf-8")


def build_confluence_sync_storage_block(
    *,
    source_type: str,
    source_root: str,
    source_relative_path: str,
    source_project: str = "",
    source_ref: str = "",
    confluence_updated_at: str = "",
    last_synced_at: str = "",
) -> str:
    sync_at = last_synced_at or _iso_now()
    project_value = source_project or "-"
    ref_value = source_ref or "-"
    return (
        '<ac:structured-macro ac:name="info"><ac:rich-text-body>'
        "<p><strong>Sync metadata</strong></p>"
        "<table><tbody>"
        f"<tr><td>source_type</td><td>{source_type}</td></tr>"
        f"<tr><td>source_project</td><td>{project_value}</td></tr>"
        f"<tr><td>source_ref</td><td>{ref_value}</td></tr>"
        f"<tr><td>source_root</td><td>{source_root}</td></tr>"
        f"<tr><td>source_markdown_file</td><td>{source_relative_path}</td></tr>"
        f"<tr><td>confluence_last_updated_at</td><td>{confluence_updated_at}</td></tr>"
        f"<tr><td>last_synced_at</td><td>{sync_at}</td></tr>"
        "</tbody></table>"
        "</ac:rich-text-body></ac:structured-macro>"
    )

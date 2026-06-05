from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace as dc_replace
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Any

from .config import AppConfig
from .confluence_client import ConfluenceClient
from .content_processing import (
    extract_image_links,
    extract_markdown_links,
    prepare_markdown_for_confluence,
    resolve_relative_markdown_path,
)
from .formatter import markdown_to_confluence_storage
from .gitlab_client import GitLabClient
from .intent import wants_rename
from .matching import rank_documents_for_page_payload
from .models import SourceDocument
from .sources import (
    load_gitlab_markdown_docs,
    load_local_markdown_docs,
    read_gitlab_asset_bytes,
    read_local_asset_bytes,
)
from .storage_merge import merge_storage_preserving_style
from .sync_meta import (
    CONTENT_PROPERTY_KEY,
    build_confluence_sync_property_value,
    build_confluence_sync_storage_block,
    build_markdown_sync_block,
    upsert_confluence_sync_storage_block,
    write_markdown_sync_block,
)


def _normalize(path: str) -> str:
    return path.replace("\\", "/")


def _semantic_hints(doc: SourceDocument) -> list[str]:
    hints: list[str] = []
    lines = doc.body.splitlines()
    for line in lines:
        if line.strip().startswith("#"):
            headline = re.sub(r"^#+\s*", "", line.strip())
            hints.append(headline)
            if ":" in headline:
                left, right = headline.split(":", 1)
                hints.append(left.strip())
                hints.append(right.strip())
            break
    hints.append(doc.title.replace("_", " "))
    dedup: list[str] = []
    seen: set[str] = set()
    for h in hints:
        key = h.strip().lower()
        if key and key not in seen:
            dedup.append(h.strip())
            seen.add(key)
    return dedup


def _planned_page_key(cfg: AppConfig, doc: SourceDocument) -> str:
    section_path = "/".join([p for p in _normalize(doc.relative_path).split("/")[:-1] if p])
    parent = cfg.confluence.parent_page_id or "ROOT"
    return f"{cfg.confluence.space_key}:{parent}:{section_path}:{doc.title}"


def detect_target_collisions(cfg: AppConfig, source: str) -> dict[str, Any]:
    docs, _ = _load_docs_and_asset_reader(cfg, source)
    by_key: dict[str, list[str]] = {}
    for doc in docs:
        key = _planned_page_key(cfg, doc)
        by_key.setdefault(key, []).append(doc.relative_path)
    collisions = [
        {"target_key": key, "documents": paths}
        for key, paths in by_key.items()
        if len(paths) > 1
    ]
    return {"source": source, "count": len(collisions), "collisions": collisions}


def _load_docs_and_asset_reader(
    cfg: AppConfig, source: str
) -> tuple[list[SourceDocument], Callable[[SourceDocument, str], bytes | None]]:
    if source == "local":
        docs = load_local_markdown_docs(cfg.local_docs_path)
        return docs, lambda doc, link: read_local_asset_bytes(cfg.local_docs_path, doc, link)
    if source == "gitlab":
        if not cfg.gitlab:
            raise ValueError("GitLab source requested but GITLAB_ENABLED is false")
        if not cfg.gitlab.project_id.strip():
            raise ValueError("GitLab source requires non-empty GITLAB_PROJECT_ID")
        gitlab = GitLabClient(cfg.gitlab.base_url, cfg.gitlab.token, cfg.gitlab.project_id, cfg.gitlab.ref)
        docs = load_gitlab_markdown_docs(gitlab, cfg.gitlab.docs_path)
        return docs, lambda doc, link: read_gitlab_asset_bytes(gitlab, doc, link)
    raise ValueError("source must be one of: local, gitlab")


def collect_documents(cfg: AppConfig, source: str) -> list[dict[str, str]]:
    docs, _ = _load_docs_and_asset_reader(cfg, source)
    return [
        {"title": d.title, "source": d.source, "path": d.path, "relative_path": d.relative_path}
        for d in docs
    ]


def build_sync_plan(cfg: AppConfig, source: str, include_link_validation: bool = True) -> dict[str, Any]:
    docs, _ = _load_docs_and_asset_reader(cfg, source)
    planned = []
    for doc in docs:
        sections = [p for p in _normalize(doc.relative_path).split("/")[:-1] if p]
        planned.append(
            {
                "relative_path": doc.relative_path,
                "title": doc.title,
                "source": doc.source,
                "sections": sections,
                "target_key": _planned_page_key(cfg, doc),
            }
        )
    out: dict[str, Any] = {"source": source, "count": len(planned), "pages": planned}
    out["collisions"] = detect_target_collisions(cfg, source)
    if include_link_validation:
        out["link_validation"] = validate_document_links(cfg, source=source, limit=500)
    return out


def _resolve_mermaid_config(confluence: ConfluenceClient, cfg: AppConfig) -> AppConfig:
    mode = (cfg.confluence.mermaid_mode or "auto").strip().lower()
    if mode not in {"auto", "forge_extension"}:
        return cfg
    if cfg.confluence.mermaid_extension_key.strip() and cfg.confluence.mermaid_extension_id.strip():
        return cfg

    discovered = confluence.discover_mermaid_extension()
    if not discovered:
        return cfg

    confluence_cfg = dc_replace(
        cfg.confluence,
        mermaid_mode="forge_extension",
        mermaid_extension_key=discovered.extension_key,
        mermaid_extension_id=discovered.extension_id,
        mermaid_extension_title=discovered.extension_title,
    )
    return dc_replace(cfg, confluence=confluence_cfg)


def sync_documents(
    cfg: AppConfig,
    source: str,
    dry_run: bool = False,
    *,
    target_page_id: str | None = None,
    parent_page_id: str | None = None,
    semantic_match: bool = False,
    intent_text: str = "",
    selected_doc_relative_path: str | None = None,
) -> dict[str, Any]:
    docs, asset_reader = _load_docs_and_asset_reader(cfg, source)
    if selected_doc_relative_path:
        docs = [d for d in docs if d.relative_path.replace("\\", "/") == selected_doc_relative_path.replace("\\", "/")]
        if not docs:
            raise ValueError(f"selected_doc_relative_path not found in source docs: {selected_doc_relative_path}")
    effective_parent = parent_page_id if parent_page_id is not None else cfg.confluence.parent_page_id

    confluence = ConfluenceClient(cfg.confluence)
    cfg = _resolve_mermaid_config(confluence, cfg)
    if cfg.confluence != confluence.cfg:
        confluence = ConfluenceClient(cfg.confluence)
    match_context: dict[str, Any] | None = None
    if target_page_id and len(docs) != 1:
        page = confluence.get_page_by_id(target_page_id, expand="version,title,_links,body.storage,ancestors")
        decision = rank_documents_for_page_payload(docs, page)
        match_context = {
            "page_id": target_page_id,
            "page_title": str(page.get("title", "")),
            "confidence": decision.confidence,
            "ambiguous": decision.ambiguous,
            "candidates": [asdict(c) for c in decision.candidates],
            "message": decision.message,
        }
        if decision.ambiguous:
            if dry_run:
                return {
                    "source": source,
                    "dry_run": True,
                    "count": len(docs),
                    "documents": collect_documents(cfg, source),
                    "collisions": detect_target_collisions(cfg, source),
                    "link_validation": validate_document_links(cfg, source=source, limit=500),
                    "target_page_id": target_page_id,
                    "effective_parent_page_id": effective_parent,
                    "semantic_match": semantic_match,
                    "matching": match_context,
                }
            return {
                "source": source,
                "dry_run": False,
                "applied": False,
                "reason": "low_confidence_markdown_match",
                "matching": match_context,
                "hint": "Specify local_docs_path to a single file/folder or provide explicit target markdown selection.",
            }
        selected = decision.selected_doc_path
        docs = [d for d in docs if d.relative_path == selected]

    if dry_run:
        return {
            "source": source,
            "dry_run": True,
            "count": len(docs),
            "documents": collect_documents(cfg, source),
            "collisions": detect_target_collisions(cfg, source),
            "link_validation": validate_document_links(cfg, source=source, limit=500),
            "target_page_id": target_page_id,
            "effective_parent_page_id": effective_parent,
            "semantic_match": semantic_match,
            "matching": match_context,
        }

    page_id_by_doc_path: dict[str, str] = {}
    page_url_by_doc_path: dict[str, str] = {}

    # Pass 1: ensure hierarchy and create/update pages to build stable page-id map.
    for doc in docs:
        parent_id = confluence.ensure_hierarchy(doc.relative_path, base_parent_id=effective_parent)
        initial_storage = markdown_to_confluence_storage(doc.body)
        preserve_title = True
        if target_page_id and len(docs) == 1:
            current = confluence.get_page_by_id(target_page_id, expand="version,title")
            preserve_title = not wants_rename(
                user_intent_text=intent_text,
                markdown_text=doc.body,
                current_page_title=str(current.get("title", "")),
            )
        upserted = confluence.upsert_page(
            doc.title,
            initial_storage,
            parent_page_id=parent_id,
            target_page_id=target_page_id if len(docs) == 1 else None,
            semantic_hints=_semantic_hints(doc),
            semantic_match=semantic_match,
            preserve_existing_title=preserve_title,
        )
        page_id_by_doc_path[doc.relative_path.replace("\\", "/")] = upserted.page_id
        page_url_by_doc_path[doc.relative_path.replace("\\", "/")] = upserted.url

    # Pass 2: resolve markdown references and upload assets/puml before final update.
    results = []
    for doc in docs:
        normalized_doc_path = doc.relative_path.replace("\\", "/")
        page_id = page_id_by_doc_path[normalized_doc_path]
        preserve_title = True
        if target_page_id and len(docs) == 1:
            current = confluence.get_page_by_id(target_page_id, expand="version,title")
            preserve_title = not wants_rename(
                user_intent_text=intent_text,
                markdown_text=doc.body,
                current_page_title=str(current.get("title", "")),
            )
        storage, uploaded = prepare_markdown_for_confluence(
            doc=doc,
            page_id=page_id,
            page_url_by_doc_path=page_url_by_doc_path,
            read_binary_asset=asset_reader,
            upload_attachment=confluence.upload_attachment,
            confluence_cfg=cfg.confluence,
        )
        if target_page_id and len(docs) == 1:
            existing = confluence.get_page_by_id(target_page_id, expand="version,title,body.storage")
            existing_storage = (
                existing.get("body", {}).get("storage", {}).get("value", "")
                if isinstance(existing.get("body"), dict)
                else ""
            )
            merged = merge_storage_preserving_style(existing_storage, storage)
            storage = merged.storage_html
            patch_info = {
                "mode": merged.mode,
                "risk_score": merged.risk_score,
                "details": merged.details,
            }
        else:
            patch_info = {"mode": "replace", "risk_score": 0.0, "details": "new or non-targeted page update"}

        parent_id = confluence.ensure_hierarchy(doc.relative_path, base_parent_id=effective_parent)
        source_project = ""
        source_ref = ""
        source_root = str(cfg.local_docs_path)
        if source == "gitlab" and cfg.gitlab:
            source_project = cfg.gitlab.project_id
            source_ref = cfg.gitlab.ref
            source_root = cfg.gitlab.docs_path
        sync_block = build_confluence_sync_storage_block(
            source_type=source,
            source_root=source_root,
            source_relative_path=doc.relative_path.replace("\\", "/"),
            source_project=source_project,
            source_ref=source_ref,
            confluence_updated_at="",
        )
        final_storage = upsert_confluence_sync_storage_block(storage, sync_block)
        upserted = confluence.upsert_page(
            doc.title,
            final_storage,
            parent_page_id=parent_id,
            target_page_id=target_page_id if len(docs) == 1 else None,
            semantic_hints=_semantic_hints(doc),
            semantic_match=semantic_match,
            preserve_existing_title=preserve_title,
        )
        confluence.set_content_property(
            upserted.page_id,
            CONTENT_PROPERTY_KEY,
            build_confluence_sync_property_value(
                source_type=source,
                source_root=source_root,
                source_relative_path=doc.relative_path.replace("\\", "/"),
                space_key=cfg.confluence.space_key,
                source_project=source_project,
                source_ref=source_ref,
                confluence_page_id=upserted.page_id,
                confluence_page_url=upserted.url,
            ),
        )
        md_sync_updated = False
        if doc.source == "local":
            block = build_markdown_sync_block(
                page_id=upserted.page_id,
                page_url=upserted.url,
                space_key=cfg.confluence.space_key,
            )
            write_markdown_sync_block(doc.path, block)
            md_sync_updated = True
        results.append(
            asdict(upserted)
            | {
                "source_path": doc.path,
                "source": doc.source,
                "relative_path": doc.relative_path,
                "parent_id": parent_id,
                "attachments_uploaded": uploaded,
                "patch": patch_info,
                "markdown_sync_updated": md_sync_updated,
            }
        )

    return {
        "source": source,
        "dry_run": False,
        "count": len(results),
        "results": results,
        "matching": match_context,
    }


def search_markdown_content(cfg: AppConfig, source: str, pattern: str, limit: int = 50) -> dict[str, Any]:
    docs, _ = _load_docs_and_asset_reader(cfg, source)
    needle = pattern.lower()
    hits: list[dict[str, str]] = []
    for doc in docs:
        if needle in doc.body.lower():
            hits.append({"title": doc.title, "relative_path": doc.relative_path, "source": doc.source})
            if len(hits) >= limit:
                break
    return {"source": source, "pattern": pattern, "count": len(hits), "hits": hits}


def validate_document_links(cfg: AppConfig, source: str, limit: int = 200) -> dict[str, Any]:
    docs, asset_reader = _load_docs_and_asset_reader(cfg, source)
    doc_paths = {d.relative_path.replace("\\", "/") for d in docs}
    issues: list[dict[str, str]] = []

    for doc in docs:
        for link in extract_markdown_links(doc.body):
            if link.startswith(("http://", "https://", "#")):
                continue
            if link.lower().endswith(".md"):
                target = resolve_relative_markdown_path(doc.relative_path, link)
                if target not in doc_paths:
                    issues.append(
                        {
                            "type": "missing_markdown_reference",
                            "doc": doc.relative_path,
                            "link": link,
                            "resolved": target,
                        }
                    )
                    if len(issues) >= limit:
                        return {"source": source, "count": len(issues), "issues": issues}

        for img_link in extract_image_links(doc.body):
            if img_link.startswith(("http://", "https://")):
                continue
            blob = asset_reader(doc, img_link)
            if blob is None:
                issues.append(
                    {
                        "type": "missing_asset_reference",
                        "doc": doc.relative_path,
                        "link": img_link,
                        "resolved": resolve_relative_markdown_path(doc.relative_path, img_link),
                    }
                )
                if len(issues) >= limit:
                    return {"source": source, "count": len(issues), "issues": issues}

    return {"source": source, "count": len(issues), "issues": issues}


def suggest_markdown_for_confluence_page(cfg: AppConfig, source: str, page_id: str) -> dict[str, Any]:
    docs, _ = _load_docs_and_asset_reader(cfg, source)
    confluence = ConfluenceClient(cfg.confluence)
    page = confluence.get_page_by_id(page_id, expand="version,title,_links,body.storage,ancestors")
    decision = rank_documents_for_page_payload(docs, page)
    links = page.get("_links", {}) if isinstance(page, dict) else {}
    return {
        "source": source,
        "page_id": page_id,
        "page_title": str(page.get("title", "")),
        "page_url": f"{cfg.confluence.base_url.rstrip('/')}{links.get('webui', '')}",
        "confidence": decision.confidence,
        "ambiguous": decision.ambiguous,
        "selected_doc_path": decision.selected_doc_path,
        "message": decision.message,
        "candidates": [asdict(c) for c in decision.candidates],
    }


def suggest_confluence_for_markdown(cfg: AppConfig, source: str, doc_relative_path: str, limit: int = 5) -> dict[str, Any]:
    docs, _ = _load_docs_and_asset_reader(cfg, source)
    normalized = doc_relative_path.replace("\\", "/")
    doc = next((d for d in docs if d.relative_path.replace("\\", "/") == normalized), None)
    if not doc:
        raise ValueError(f"Document not found: {doc_relative_path}")
    confluence = ConfluenceClient(cfg.confluence)
    hints = _semantic_hints(doc)
    rows = confluence.search_pages(doc.title, limit=max(10, limit * 2))
    scored: list[dict[str, Any]] = []
    for row in rows:
        t = str(row.get("title", ""))
        score = 0.65 * SequenceMatcher(None, doc.title.lower(), t.lower()).ratio()
        if hints:
            score += 0.35 * max(SequenceMatcher(None, h.lower(), t.lower()).ratio() for h in hints)
        scored.append(
            {
                "page_id": str(row.get("id", "")),
                "title": t,
                "url": str(row.get("url", "")),
                "score": round(min(score, 1.0), 4),
            }
        )
    scored.sort(key=lambda x: float(x["score"]), reverse=True)
    top = scored[0]["score"] if scored else 0.0
    second = scored[1]["score"] if len(scored) > 1 else 0.0
    ambiguous = top < 0.35 or (top - second) < 0.08
    return {
        "source": source,
        "doc_relative_path": doc.relative_path,
        "doc_title": doc.title,
        "ambiguous": ambiguous,
        "confidence": top,
        "selected_page_id": None if ambiguous or not scored else scored[0]["page_id"],
        "candidates": scored[:limit],
    }


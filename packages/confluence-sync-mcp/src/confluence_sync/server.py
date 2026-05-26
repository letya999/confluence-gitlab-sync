from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .config import build_runtime_config
from .confluence_client import ConfluenceClient
from .confluence_export import ExportOptions, export_confluence_page
from .gitlab_client import GitLabClient
from .sync_service import (
    build_sync_plan,
    collect_documents,
    detect_target_collisions,
    search_markdown_content,
    suggest_confluence_for_markdown,
    suggest_markdown_for_confluence_page,
    sync_documents,
    validate_document_links,
)

mcp = FastMCP("confluence-sync-mcp")


@mcp.tool()
def list_docs(
    source: str = "local",
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """List markdown documents planned for sync from local or GitLab source."""
    cfg = build_runtime_config(
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    docs = collect_documents(cfg, source)
    return {"source": source, "count": len(docs), "documents": docs}


@mcp.tool()
def search_docs(
    source: str = "local",
    pattern: str = "",
    limit: int = 50,
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """Search markdown content in local or GitLab source before publishing."""
    if not pattern.strip():
        raise ValueError("pattern must not be empty")
    cfg = build_runtime_config(
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    return search_markdown_content(cfg, source=source, pattern=pattern, limit=limit)


@mcp.tool()
def search_confluence_pages(query: str, limit: int = 25, space_key: str = "") -> dict:
    """Search existing Confluence pages in configured space."""
    if not query.strip():
        raise ValueError("query must not be empty")
    cfg = build_runtime_config(space_key=space_key or None)
    client = ConfluenceClient(cfg.confluence)
    results = client.search_pages(query, limit=limit)
    return {"query": query, "count": len(results), "results": results}


@mcp.tool()
def find_semantic_confluence_match(
    title: str,
    hints: list[str] | None = None,
    min_score: float = 0.45,
    space_key: str = "",
) -> dict:
    """Find the best semantic page match in Confluence by title + optional hints."""
    if not title.strip():
        raise ValueError("title must not be empty")
    cfg = build_runtime_config(space_key=space_key or None)
    client = ConfluenceClient(cfg.confluence)
    match = client.find_best_semantic_page_match(
        title=title.strip(),
        hints=hints or [],
        min_score=min_score,
    )
    if not match:
        return {"matched": False}
    links = match.get("_links", {})
    return {
        "matched": True,
        "page_id": str(match.get("id", "")),
        "title": str(match.get("title", "")),
        "url": f"{cfg.confluence.base_url.rstrip('/')}{links.get('webui', '')}",
    }


@mcp.tool()
def suggest_markdown_match_for_page(
    page_id: str,
    source: str = "local",
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """Suggest best markdown candidates for a specific Confluence page."""
    if not page_id.strip():
        raise ValueError("page_id must not be empty")
    cfg = build_runtime_config(
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    return suggest_markdown_for_confluence_page(cfg, source=source, page_id=page_id.strip())


@mcp.tool()
def suggest_confluence_match_for_markdown(
    doc_relative_path: str,
    source: str = "local",
    limit: int = 5,
    space_key: str = "",
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """Suggest best Confluence page candidates for a markdown document."""
    if not doc_relative_path.strip():
        raise ValueError("doc_relative_path must not be empty")
    cfg = build_runtime_config(
        space_key=space_key or None,
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    return suggest_confluence_for_markdown(
        cfg,
        source=source,
        doc_relative_path=doc_relative_path.strip(),
        limit=limit,
    )


@mcp.tool()
def export_from_confluence(
    page_id: str,
    output_dir: str = "",
    space_key: str = "",
    include_attachments: bool = True,
    extract_mermaid: bool = True,
    extract_plantuml: bool = True,
    output_mode: str = "single_markdown",
) -> dict:
    """Export Confluence page to local Markdown (+ optional puml/attachments) for local or GitLab docs workflows."""
    if not page_id.strip():
        raise ValueError("page_id must not be empty")
    cfg = build_runtime_config(space_key=space_key or None)
    client = ConfluenceClient(cfg.confluence)
    target_dir = output_dir.strip() or str(cfg.local_docs_path)
    options = ExportOptions(
        include_attachments=include_attachments,
        extract_mermaid=extract_mermaid,
        extract_plantuml=extract_plantuml,
        output_mode=output_mode,
    )
    from pathlib import Path

    return export_confluence_page(client, page_id=page_id.strip(), output_dir=Path(target_dir).resolve(), options=options)


@mcp.tool()
def validate_links(
    source: str = "local",
    limit: int = 200,
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """Validate markdown references and asset links before sync."""
    cfg = build_runtime_config(
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    return validate_document_links(cfg, source=source, limit=limit)


@mcp.tool()
def plan_sync(
    source: str = "local",
    space_key: str = "",
    parent_page_id: str = "",
    parent_title_path: str = "",
    create_missing_parent_path: bool = False,
    target_page_id: str = "",
    semantic_match: bool = False,
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
    include_link_validation: bool = True,
) -> dict:
    """Build AI-readable migration plan with hierarchy, collisions, and link checks."""
    cfg = build_runtime_config(
        space_key=space_key or None,
        parent_page_id=parent_page_id if parent_page_id != "" else None,
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    if parent_title_path.strip():
        client = ConfluenceClient(cfg.confluence)
        resolved = client.ensure_parent_title_path(
            parent_title_path.strip(),
            create_missing=create_missing_parent_path,
        )
        if not resolved:
            return {
                "source": source,
                "count": 0,
                "error": "parent_title_path_not_found",
                "parent_title_path": parent_title_path,
            }
        cfg = build_runtime_config(
            space_key=cfg.confluence.space_key,
            parent_page_id=resolved,
            local_docs_path=str(cfg.local_docs_path),
            gitlab_project_id=cfg.gitlab.project_id if cfg.gitlab else None,
            gitlab_ref=cfg.gitlab.ref if cfg.gitlab else None,
            gitlab_docs_path=cfg.gitlab.docs_path if cfg.gitlab else None,
        )
    out = build_sync_plan(cfg, source=source, include_link_validation=include_link_validation)
    out["effective_parent_page_id"] = cfg.confluence.parent_page_id
    out["target_page_id"] = target_page_id or None
    out["semantic_match"] = semantic_match
    return out


@mcp.tool()
def resolve_parent_page_id(parent_title: str, space_key: str = "") -> dict:
    """Resolve Confluence parent page id by exact title in configured space."""
    if not parent_title.strip():
        raise ValueError("parent_title must not be empty")
    cfg = build_runtime_config(space_key=space_key or None)
    client = ConfluenceClient(cfg.confluence)
    page_id = client.resolve_parent_page_id(parent_title.strip())
    return {"parent_title": parent_title, "space_key": cfg.confluence.space_key, "parent_page_id": page_id}


@mcp.tool()
def resolve_gitlab_project(
    query: str,
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """Search GitLab projects using MCP-compatible env (GITLAB_API_URL + PAT)."""
    if not query.strip():
        raise ValueError("query must not be empty")
    cfg = build_runtime_config(
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    if not cfg.gitlab:
        raise ValueError("GitLab is not configured. Set GITLAB_ENABLED=true and token/url env vars.")
    client = GitLabClient(cfg.gitlab.base_url, cfg.gitlab.token, cfg.gitlab.project_id, cfg.gitlab.ref)
    rows = client.search_projects(query)
    return {"query": query, "count": len(rows), "projects": rows}


@mcp.tool()
def smoke_check(
    confluence_query: str = "a",
    gitlab_query: str = "a",
    space_key: str = "",
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
) -> dict:
    """Run connectivity/readiness checks for Confluence and GitLab before sync."""
    cfg = build_runtime_config(
        space_key=space_key or None,
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    result: dict = {"confluence": {"ok": False}, "gitlab": {"ok": False}}
    try:
        cc = ConfluenceClient(cfg.confluence)
        rows = cc.search_pages(confluence_query, limit=3)
        result["confluence"] = {"ok": True, "query": confluence_query, "count": len(rows)}
    except Exception as exc:
        result["confluence"] = {"ok": False, "error": str(exc)}

    try:
        if not cfg.gitlab:
            raise ValueError("GITLAB_ENABLED is false")
        gc = GitLabClient(cfg.gitlab.base_url, cfg.gitlab.token, cfg.gitlab.project_id or "1", cfg.gitlab.ref)
        rows = gc.search_projects(gitlab_query, per_page=3)
        result["gitlab"] = {"ok": True, "query": gitlab_query, "count": len(rows)}
    except Exception as exc:
        result["gitlab"] = {"ok": False, "error": str(exc)}

    return result


@mcp.tool()
def sync_to_confluence(
    source: str = "local",
    dry_run: bool = False,
    space_key: str = "",
    parent_page_id: str = "",
    parent_title_path: str = "",
    create_missing_parent_path: bool = False,
    target_page_id: str = "",
    semantic_match: bool = False,
    local_docs_path: str = "",
    gitlab_project_id: str = "",
    gitlab_ref: str = "",
    gitlab_docs_path: str = "",
    selected_doc_relative_path: str = "",
    intent_text: str = "",
) -> dict:
    """Sync markdown documents to Confluence space using create-or-update strategy."""
    cfg = build_runtime_config(
        space_key=space_key or None,
        parent_page_id=parent_page_id if parent_page_id != "" else None,
        local_docs_path=local_docs_path or None,
        gitlab_project_id=gitlab_project_id or None,
        gitlab_ref=gitlab_ref or None,
        gitlab_docs_path=gitlab_docs_path or None,
    )
    if parent_title_path.strip():
        client = ConfluenceClient(cfg.confluence)
        resolved = client.ensure_parent_title_path(
            parent_title_path.strip(),
            create_missing=create_missing_parent_path,
        )
        if not resolved:
            return {
                "source": source,
                "dry_run": dry_run,
                "applied": False,
                "reason": "parent_title_path_not_found",
                "parent_title_path": parent_title_path,
            }
        cfg = build_runtime_config(
            space_key=cfg.confluence.space_key,
            parent_page_id=resolved,
            local_docs_path=str(cfg.local_docs_path),
            gitlab_project_id=cfg.gitlab.project_id if cfg.gitlab else None,
            gitlab_ref=cfg.gitlab.ref if cfg.gitlab else None,
            gitlab_docs_path=cfg.gitlab.docs_path if cfg.gitlab else None,
        )
    collisions = detect_target_collisions(cfg, source=source)
    if collisions["count"] > 0 and not dry_run:
        return {
            "source": source,
            "dry_run": False,
            "applied": False,
            "reason": "target_collisions_detected",
            "collisions": collisions,
            "hint": "Run plan_sync and resolve collisions before apply.",
        }
    return sync_documents(
        cfg,
        source=source,
        dry_run=dry_run,
        target_page_id=target_page_id.strip() or None,
        parent_page_id=cfg.confluence.parent_page_id,
        semantic_match=semantic_match,
        selected_doc_relative_path=selected_doc_relative_path.strip() or None,
        intent_text=intent_text.strip(),
    )


@mcp.prompt()
def migration_operator_prompt(task: str, source: str = "local") -> str:
    """Generate operator prompt for AI-controlled Confluence migration flow."""
    return (
        "You operate Confluence migration via MCP tools. "
        f"Task: {task}. Source: {source}. "
        "Always call plan_sync first, review collisions/link_validation and hierarchy, "
        "then call sync_to_confluence with dry_run=true, and only then dry_run=false."
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()


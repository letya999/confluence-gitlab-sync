from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from confluence_sync.config import load_config
from confluence_sync.sync_service import sync_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one-shot sync to Confluence without MCP client")
    parser.add_argument("--source", choices=["local", "gitlab"], default="local")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--space-key", default="")
    parser.add_argument("--parent-page-id", default="")
    parser.add_argument("--parent-title-path", default="")
    parser.add_argument("--create-missing-parent-path", action="store_true")
    parser.add_argument("--target-page-id", default="")
    parser.add_argument("--semantic-match", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    if args.space_key or args.parent_page_id:
        from confluence_sync.config import build_runtime_config

        cfg = build_runtime_config(
            space_key=args.space_key or None,
            parent_page_id=args.parent_page_id if args.parent_page_id != "" else None,
            local_docs_path=str(cfg.local_docs_path),
            gitlab_project_id=cfg.gitlab.project_id if cfg.gitlab else None,
            gitlab_ref=cfg.gitlab.ref if cfg.gitlab else None,
            gitlab_docs_path=cfg.gitlab.docs_path if cfg.gitlab else None,
        )
    if args.parent_title_path.strip():
        from confluence_sync.confluence_client import ConfluenceClient
        from confluence_sync.config import build_runtime_config

        client = ConfluenceClient(cfg.confluence)
        resolved = client.ensure_parent_title_path(
            args.parent_title_path.strip(),
            create_missing=args.create_missing_parent_path,
        )
        if not resolved:
            raise ValueError("parent_title_path not found and create_missing_parent_path is false")
        cfg = build_runtime_config(
            space_key=cfg.confluence.space_key,
            parent_page_id=resolved,
            local_docs_path=str(cfg.local_docs_path),
            gitlab_project_id=cfg.gitlab.project_id if cfg.gitlab else None,
            gitlab_ref=cfg.gitlab.ref if cfg.gitlab else None,
            gitlab_docs_path=cfg.gitlab.docs_path if cfg.gitlab else None,
        )
    result = sync_documents(
        cfg,
        source=args.source,
        dry_run=args.dry_run,
        target_page_id=args.target_page_id.strip() or None,
        parent_page_id=cfg.confluence.parent_page_id,
        semantic_match=args.semantic_match,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from confluence_sync.config import build_runtime_config
from confluence_sync.confluence_client import ConfluenceClient
from confluence_sync.confluence_export import ExportOptions, export_confluence_page


def main() -> None:
    parser = argparse.ArgumentParser(description="Export one Confluence page to markdown assets")
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--space-key", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--mode", default="single_markdown", choices=["single_markdown", "markdown_with_assets", "markdown_for_gitlab_docs"])
    parser.add_argument("--no-attachments", action="store_true")
    parser.add_argument("--no-mermaid", action="store_true")
    parser.add_argument("--no-plantuml", action="store_true")
    args = parser.parse_args()

    cfg = build_runtime_config(space_key=args.space_key or None)
    client = ConfluenceClient(cfg.confluence)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else cfg.local_docs_path
    result = export_confluence_page(
        client,
        page_id=args.page_id,
        output_dir=output_dir,
        options=ExportOptions(
            include_attachments=not args.no_attachments,
            extract_mermaid=not args.no_mermaid,
            extract_plantuml=not args.no_plantuml,
            output_mode=args.mode,
        ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

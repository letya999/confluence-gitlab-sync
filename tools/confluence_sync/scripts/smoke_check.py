from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from confluence_sync.config import load_config
from confluence_sync.confluence_client import ConfluenceClient
from confluence_sync.gitlab_client import GitLabClient


def main() -> None:
    cfg = load_config()
    out: dict = {"confluence": {"ok": False}, "gitlab": {"ok": False}}
    try:
        cc = ConfluenceClient(cfg.confluence)
        rows = cc.search_pages("a", limit=3)
        out["confluence"] = {"ok": True, "count": len(rows)}
    except Exception as exc:
        out["confluence"] = {"ok": False, "error": str(exc)}

    try:
        if not cfg.gitlab:
            raise ValueError("GITLAB_ENABLED is false")
        gc = GitLabClient(cfg.gitlab.base_url, cfg.gitlab.token, cfg.gitlab.project_id or "1", cfg.gitlab.ref)
        rows = gc.search_projects("a", per_page=3)
        out["gitlab"] = {"ok": True, "count": len(rows)}
    except Exception as exc:
        out["gitlab"] = {"ok": False, "error": str(exc)}

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


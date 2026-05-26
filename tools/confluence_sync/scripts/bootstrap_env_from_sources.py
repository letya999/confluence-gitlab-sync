from __future__ import annotations

import argparse
import os
from pathlib import Path


def parse_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k] = v
    return out


def parse_toml_kv(path: Path, keys: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        if k not in keys:
            continue
        out[k] = v.strip().strip('"').strip("'")
    return out


def _resolve_default_codex_config() -> Path:
    codex_home = os.getenv("CODEX_HOME", "").strip()
    if codex_home:
        return Path(codex_home) / "config.toml"
    return Path.home() / ".codex" / "config.toml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap confluence_sync .env from existing env/config files")
    parser.add_argument("--source-env", default="", help="Path to source .env with Jira/Confluence values")
    parser.add_argument("--codex-config", default="", help="Path to Codex config.toml with GitLab MCP values")
    parser.add_argument("--out", default="", help="Output .env path (defaults to tools/confluence_sync/.env)")
    parser.add_argument(
        "--local-docs-path",
        default="./docs",
        help="Default LOCAL_DOCS_PATH to write when not present in source env",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    env_src = Path(args.source_env).expanduser() if args.source_env else Path(".env")
    codex_cfg = (
        Path(args.codex_config).expanduser() if args.codex_config else _resolve_default_codex_config()
    )
    out_path = (
        Path(args.out).expanduser()
        if args.out
        else Path(__file__).resolve().parents[1] / ".env"
    )

    env = parse_dotenv(env_src) if env_src.exists() else {}
    cfg = parse_toml_kv(codex_cfg, {"GITLAB_API_URL", "GITLAB_PERSONAL_ACCESS_TOKEN"}) if codex_cfg.exists() else {}

    jira_base = env.get("JIRA_BASE_URL", "").rstrip("/")
    confluence_base = f"{jira_base}/wiki" if jira_base and not jira_base.lower().endswith("/wiki") else jira_base
    gl_api = cfg.get("GITLAB_API_URL", "")
    gl_base = gl_api[:-7] if gl_api.endswith("/api/v4") else gl_api

    content = "\n".join(
        [
            f"CONFLUENCE_BASE_URL={confluence_base or 'https://your-domain.atlassian.net/wiki'}",
            "CONFLUENCE_SPACE_KEY=ARCH",
            "CONFLUENCE_PARENT_PAGE_ID=",
            f"CONFLUENCE_USERNAME={env.get('JIRA_USER_EMAIL', '')}",
            f"CONFLUENCE_API_TOKEN={env.get('JIRA_API_TOKEN', '')}",
            "",
            f"LOCAL_DOCS_PATH={args.local_docs_path}",
            "",
            "GITLAB_ENABLED=false",
            f"GITLAB_BASE_URL={gl_base or 'https://gitlab.com'}",
            "GITLAB_PROJECT_ID=",
            f"GITLAB_TOKEN={cfg.get('GITLAB_PERSONAL_ACCESS_TOKEN', '')}",
            "GITLAB_REF=main",
            "GITLAB_DOCS_PATH=docs",
            "",
        ]
    )
    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()


from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import replace as dc_replace
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class ConfluenceConfig:
    base_url: str
    space_key: str
    parent_page_id: str | None
    username: str
    api_token: str
    mermaid_mode: str = "svg"
    mermaid_macro_name: str = "mermaid-cloud"
    mermaid_extension_key: str = ""
    mermaid_extension_id: str = ""
    mermaid_extension_title: str = "Mermaid Diagram"
    plantuml_mode: str = "svg"
    plantuml_macro_name: str = "plantumlcloud"


@dataclass(frozen=True)
class GitLabConfig:
    base_url: str
    project_id: str
    token: str
    ref: str
    docs_path: str


@dataclass(frozen=True)
class AppConfig:
    confluence: ConfluenceConfig
    local_docs_path: Path
    gitlab: GitLabConfig | None


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _required_any(names: list[str]) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    raise ValueError(f"Missing required env var from: {', '.join(names)}")


def load_config() -> AppConfig:
    load_dotenv()
    base_url = _required_any(["CONFLUENCE_BASE_URL", "JIRA_BASE_URL"])
    if "/wiki" not in base_url.rstrip("/").lower():
        base_url = f"{base_url.rstrip('/')}/wiki"

    confluence = ConfluenceConfig(
        base_url=base_url,
        space_key=_required("CONFLUENCE_SPACE_KEY"),
        parent_page_id=os.getenv("CONFLUENCE_PARENT_PAGE_ID", "").strip() or None,
        username=_required_any(["CONFLUENCE_USERNAME", "JIRA_USER_EMAIL"]),
        api_token=_required_any(["CONFLUENCE_API_TOKEN", "JIRA_API_TOKEN"]),
        mermaid_mode=os.getenv("CONFLUENCE_MERMAID_MODE", "svg").strip() or "svg",
        mermaid_macro_name=os.getenv("CONFLUENCE_MERMAID_MACRO_NAME", "mermaid-cloud").strip() or "mermaid-cloud",
        mermaid_extension_key=os.getenv("CONFLUENCE_MERMAID_EXTENSION_KEY", "").strip(),
        mermaid_extension_id=os.getenv("CONFLUENCE_MERMAID_EXTENSION_ID", "").strip(),
        mermaid_extension_title=os.getenv("CONFLUENCE_MERMAID_EXTENSION_TITLE", "Mermaid Diagram").strip()
        or "Mermaid Diagram",
        plantuml_mode=os.getenv("CONFLUENCE_PLANTUML_MODE", "svg").strip() or "svg",
        plantuml_macro_name=os.getenv("CONFLUENCE_PLANTUML_MACRO_NAME", "plantumlcloud").strip() or "plantumlcloud",
    )

    local_docs_path = Path(os.getenv("LOCAL_DOCS_PATH", "./docs")).resolve()

    gitlab_enabled = os.getenv("GITLAB_ENABLED", "false").strip().lower() == "true"
    gitlab = None
    if gitlab_enabled:
        gitlab = GitLabConfig(
            base_url=_required_any(["GITLAB_BASE_URL", "GITLAB_API_URL"]),
            project_id=os.getenv("GITLAB_PROJECT_ID", "").strip(),
            token=_required_any(["GITLAB_TOKEN", "GITLAB_PERSONAL_ACCESS_TOKEN"]),
            ref=os.getenv("GITLAB_REF", "main").strip() or "main",
            docs_path=os.getenv("GITLAB_DOCS_PATH", "docs").strip() or "docs",
        )

    return AppConfig(confluence=confluence, local_docs_path=local_docs_path, gitlab=gitlab)


def build_runtime_config(
    *,
    space_key: str | None = None,
    parent_page_id: str | None = None,
    local_docs_path: str | None = None,
    gitlab_project_id: str | None = None,
    gitlab_ref: str | None = None,
    gitlab_docs_path: str | None = None,
) -> AppConfig:
    cfg = load_config()
    confluence = cfg.confluence
    gitlab = cfg.gitlab
    docs_path = cfg.local_docs_path

    if space_key:
        confluence = dc_replace(confluence, space_key=space_key.strip())
    if parent_page_id is not None:
        normalized_parent = parent_page_id.strip()
        confluence = dc_replace(confluence, parent_page_id=normalized_parent or None)
    if local_docs_path:
        docs_path = Path(local_docs_path).resolve()

    if gitlab and (gitlab_project_id or gitlab_ref or gitlab_docs_path):
        gitlab = dc_replace(
            gitlab,
            project_id=gitlab_project_id.strip() if gitlab_project_id else gitlab.project_id,
            ref=gitlab_ref.strip() if gitlab_ref else gitlab.ref,
            docs_path=gitlab_docs_path.strip() if gitlab_docs_path else gitlab.docs_path,
        )

    return AppConfig(confluence=confluence, local_docs_path=docs_path, gitlab=gitlab)


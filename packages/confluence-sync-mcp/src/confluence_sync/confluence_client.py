from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

import requests

from .config import ConfluenceConfig


@dataclass
class UpsertResult:
    title: str
    page_id: str
    action: str
    url: str


@dataclass(frozen=True)
class MermaidExtension:
    extension_key: str
    extension_id: str
    extension_title: str


class ConfluenceClient:
    _MERMAID_EXTENSION_RE = re.compile(
        r"<ac:adf-extension>.*?"
        r"<ac:adf-attribute key=\"extension-key\">(?P<key>.*?)</ac:adf-attribute>.*?"
        r"<ac:adf-parameter key=\"extension-id\">(?P<id>.*?)</ac:adf-parameter>.*?"
        r"<ac:adf-parameter key=\"extension-title\">(?P<title>.*?)</ac:adf-parameter>.*?"
        r"<ac:adf-parameter key=\"diagram-source\">(?P<source>.*?)</ac:adf-parameter>.*?"
        r"</ac:adf-extension>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, cfg: ConfluenceConfig) -> None:
        self.cfg = cfg
        self.base = cfg.base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (cfg.username, cfg.api_token)
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
        self._mermaid_extension_cache: MermaidExtension | None | bool = False

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        resp = self.session.request(method, f"{self.base}{path}", timeout=60, **kwargs)
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict):
            raise ValueError("Confluence API returned non-object JSON payload")
        return payload

    def find_page_by_title(self, title: str) -> dict[str, Any] | None:
        payload = self._request(
            "GET",
            "/rest/api/content",
            params={"spaceKey": self.cfg.space_key, "title": title, "expand": "version"},
        )
        items = payload.get("results", [])
        return items[0] if items else None

    def get_page_by_id(self, page_id: str, expand: str = "version,title,_links") -> dict[str, Any]:
        return self._request("GET", f"/rest/api/content/{page_id}", params={"expand": expand})

    def get_content_property(self, page_id: str, key: str) -> dict[str, Any] | None:
        resp = self.session.get(f"{self.base}/rest/api/content/{page_id}/property/{key}", timeout=60)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict):
            raise ValueError("Confluence API returned non-object JSON payload")
        return payload

    def set_content_property(self, page_id: str, key: str, value: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_content_property(page_id, key)
        if existing:
            body = {
                "key": key,
                "value": value,
                "version": {"number": int(existing.get("version", {}).get("number", 0)) + 1},
            }
            return self._request("PUT", f"/rest/api/content/{page_id}/property/{key}", json=body)

        body = {"key": key, "value": value}
        return self._request("POST", f"/rest/api/content/{page_id}/property", json=body)

    def find_page_by_title_in_space(self, title: str) -> dict[str, Any] | None:
        return self.find_page_by_title(title)

    def search_pages(self, query: str, limit: int = 25) -> list[dict[str, str]]:
        cql = f'type=page and space="{self.cfg.space_key}" and title ~ "{query}"'
        payload = self._request(
            "GET",
            "/rest/api/search",
            params={"cql": cql, "limit": min(max(limit, 1), 100)},
        )
        rows: list[dict[str, str]] = []
        for item in payload.get("results", []):
            content = item.get("content", {})
            links = content.get("_links", {})
            rows.append(
                {
                    "id": str(content.get("id", "")),
                    "title": str(content.get("title", "")),
                    "url": f"{self.base}{links.get('webui', '')}",
                }
            )
        return rows

    @staticmethod
    def _normalize_text(text: str) -> str:
        lowered = text.lower()
        cleaned = re.sub(r"[^a-zа-яё0-9\s]+", " ", lowered, flags=re.IGNORECASE)
        compact = re.sub(r"\s+", " ", cleaned).strip()
        return compact

    def search_pages_verbose(self, query: str, limit: int = 25) -> list[dict[str, str | float]]:
        cql = f'type=page and space="{self.cfg.space_key}" and title ~ "{query}"'
        payload = self._request(
            "GET",
            "/rest/api/search",
            params={"cql": cql, "limit": min(max(limit, 1), 100)},
        )
        rows: list[dict[str, str | float]] = []
        for item in payload.get("results", []):
            content = item.get("content", {})
            links = content.get("_links", {})
            rows.append(
                {
                    "id": str(content.get("id", "")),
                    "title": str(content.get("title", "")),
                    "url": f"{self.base}{links.get('webui', '')}",
                    "excerpt": str(item.get("excerpt", "")),
                }
            )
        return rows

    @classmethod
    def _extract_mermaid_extension(cls, storage_html: str) -> MermaidExtension | None:
        match = cls._MERMAID_EXTENSION_RE.search(storage_html)
        if not match:
            return None
        source = match.group("source")
        if not source.strip():
            return None
        return MermaidExtension(
            extension_key=match.group("key").strip(),
            extension_id=match.group("id").strip(),
            extension_title=match.group("title").strip() or "Mermaid Diagram",
        )

    def discover_mermaid_extension(self, limit: int = 25) -> MermaidExtension | None:
        if self._mermaid_extension_cache is not False:
            return self._mermaid_extension_cache or None

        payload = self._request(
            "GET",
            "/rest/api/search",
            params={
                "cql": 'type=page and siteSearch ~ "mermaid"',
                "limit": min(max(limit, 1), 100),
                "expand": "content.body.storage,content.title",
            },
        )
        for item in payload.get("results", []):
            content = item.get("content", {})
            storage_html = str(content.get("body", {}).get("storage", {}).get("value", ""))
            discovered = self._extract_mermaid_extension(storage_html)
            if discovered:
                self._mermaid_extension_cache = discovered
                return discovered

        self._mermaid_extension_cache = None
        return None

    def find_best_semantic_page_match(
        self,
        *,
        title: str,
        hints: list[str] | None = None,
        min_score: float = 0.45,
        limit_per_query: int = 20,
    ) -> dict[str, Any] | None:
        queries = [title] + (hints or [])
        candidates: dict[str, dict[str, Any]] = {}
        for q in queries:
            qn = self._normalize_text(q)
            if not qn:
                continue
            for row in self.search_pages_verbose(q, limit=limit_per_query):
                cid = str(row["id"])
                title_norm = self._normalize_text(str(row["title"]))
                excerpt_norm = self._normalize_text(str(row.get("excerpt", "")))
                title_score = SequenceMatcher(None, qn, title_norm).ratio()
                excerpt_score = SequenceMatcher(None, qn, excerpt_norm).ratio() if excerpt_norm else 0.0
                score = max(title_score, 0.7 * title_score + 0.3 * excerpt_score)
                prev = candidates.get(cid)
                if prev is None or score > float(prev["score"]):
                    candidates[cid] = {
                        "id": cid,
                        "title": row["title"],
                        "url": row["url"],
                        "score": score,
                    }
        if not candidates:
            return None
        best = max(candidates.values(), key=lambda x: float(x["score"]))
        if float(best["score"]) < min_score:
            return None
        return self.get_page_by_id(str(best["id"]), expand="version,title,_links")

    def resolve_parent_page_id(self, title: str) -> str | None:
        page = self.find_page_by_title_in_space(title)
        return str(page["id"]) if page else None

    def resolve_parent_by_title_path(self, title_path: str) -> str | None:
        parts = [p.strip() for p in title_path.split("/") if p.strip()]
        if not parts:
            return self.cfg.parent_page_id

        current_parent = self.cfg.parent_page_id
        for title in parts:
            if current_parent:
                page = self.find_child_page_by_title(current_parent, title)
            else:
                page = self.find_page_by_title_in_space(title)
            if not page:
                return None
            current_parent = str(page["id"])
        return current_parent

    def find_child_page_by_title(self, parent_page_id: str, title: str) -> dict[str, Any] | None:
        payload = self._request(
            "GET",
            f"/rest/api/content/{parent_page_id}/child/page",
            params={"title": title, "expand": "version"},
        )
        items = payload.get("results", [])
        return items[0] if items else None

    def create_page(self, title: str, storage_value: str, parent_page_id: str | None = None) -> UpsertResult:
        body: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": self.cfg.space_key},
            "body": {"storage": {"value": storage_value, "representation": "storage"}},
        }
        effective_parent = parent_page_id or self.cfg.parent_page_id
        if effective_parent:
            body["ancestors"] = [{"id": effective_parent}]

        created = self._request("POST", "/rest/api/content", json=body)
        return UpsertResult(
            title=title,
            page_id=created["id"],
            action="created",
            url=f"{self.base}{created['_links']['webui']}",
        )

    def update_page(self, page: dict[str, Any], title: str, storage_value: str) -> UpsertResult:
        page_id = page["id"]
        version = int(page["version"]["number"]) + 1
        body = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": {"number": version},
            "body": {"storage": {"value": storage_value, "representation": "storage"}},
        }
        updated = self._request("PUT", f"/rest/api/content/{page_id}", json=body)
        return UpsertResult(
            title=title,
            page_id=page_id,
            action="updated",
            url=f"{self.base}{updated['_links']['webui']}",
        )

    def update_page_by_id(
        self,
        page_id: str,
        title: str,
        storage_value: str,
        *,
        preserve_existing_title: bool = True,
    ) -> UpsertResult:
        page = self.get_page_by_id(page_id, expand="version,title")
        effective_title = str(page.get("title", title)) if preserve_existing_title else title
        return self.update_page(page=page, title=effective_title, storage_value=storage_value)

    def upsert_page(
        self,
        title: str,
        storage_value: str,
        parent_page_id: str | None = None,
        target_page_id: str | None = None,
        semantic_hints: list[str] | None = None,
        semantic_match: bool = False,
        preserve_existing_title: bool = True,
    ) -> UpsertResult:
        if target_page_id:
            return self.update_page_by_id(
                target_page_id,
                title=title,
                storage_value=storage_value,
                preserve_existing_title=preserve_existing_title,
            )
        existing = None
        effective_parent = parent_page_id or self.cfg.parent_page_id
        if effective_parent:
            existing = self.find_child_page_by_title(effective_parent, title)
        if existing is None and effective_parent is None:
            existing = self.find_page_by_title(title)
        if existing is None and semantic_match:
            existing = self.find_best_semantic_page_match(title=title, hints=semantic_hints or [])
        if existing:
            return self.update_page(existing, title, storage_value)
        return self.create_page(title, storage_value, parent_page_id=effective_parent)

    def upload_attachment(self, page_id: str, filename: str, content: bytes) -> dict[str, str]:
        url = f"{self.base}/rest/api/content/{page_id}/child/attachment"
        headers = {"X-Atlassian-Token": "nocheck"}
        files = {"file": (filename, content)}
        resp = self.session.post(url, headers=headers, files=files, timeout=120)
        resp.raise_for_status()
        payload = resp.json()
        item = payload.get("results", [{}])[0]
        download_link = item.get("_links", {}).get("download", "")
        return {
            "filename": filename,
            "download_url": f"{self.base}{download_link}" if download_link else "",
        }

    def list_attachments(self, page_id: str, limit: int = 200) -> list[dict[str, str]]:
        payload = self._request(
            "GET",
            f"/rest/api/content/{page_id}/child/attachment",
            params={"limit": min(max(limit, 1), 500)},
        )
        rows: list[dict[str, str]] = []
        for item in payload.get("results", []):
            title = str(item.get("title", ""))
            links = item.get("_links", {})
            download = str(links.get("download", ""))
            rows.append(
                {
                    "id": str(item.get("id", "")),
                    "title": title,
                    "download_url": f"{self.base}{download}" if download else "",
                }
            )
        return rows

    def download_attachment(self, download_url: str) -> bytes:
        resp = self.session.get(download_url, timeout=120)
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def section_titles_from_relative_path(relative_path: str) -> list[str]:
        parts = [p for p in relative_path.replace("\\", "/").split("/")[:-1] if p and p != "."]
        return [part.replace("_", " ").replace("-", " ").strip().title() for part in parts]

    def ensure_hierarchy(self, relative_path: str, base_parent_id: str | None = None) -> str | None:
        effective_parent = base_parent_id if base_parent_id is not None else self.cfg.parent_page_id
        for section_title in self.section_titles_from_relative_path(relative_path):
            placeholder = "<p>Auto-generated section page for imported documents.</p>"
            upserted = self.upsert_page(section_title, placeholder, parent_page_id=effective_parent)
            effective_parent = upserted.page_id
        return effective_parent

    def ensure_parent_title_path(self, title_path: str, create_missing: bool = False) -> str | None:
        parts = [p.strip() for p in title_path.split("/") if p.strip()]
        if not parts:
            return self.cfg.parent_page_id
        current_parent = self.cfg.parent_page_id
        for title in parts:
            page = self.find_child_page_by_title(current_parent, title) if current_parent else self.find_page_by_title_in_space(title)
            if not page:
                if not create_missing:
                    return None
                placeholder = "<p>Auto-generated parent section page.</p>"
                created = self.create_page(title, placeholder, parent_page_id=current_parent)
                current_parent = created.page_id
                continue
            current_parent = str(page["id"])
        return current_parent


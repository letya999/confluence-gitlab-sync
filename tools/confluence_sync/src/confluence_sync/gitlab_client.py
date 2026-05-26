from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests


class GitLabClient:
    def __init__(self, base_url: str, token: str, project_id: str, ref: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.project_id = quote(project_id, safe="")
        self.ref = ref
        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": token, "Accept": "application/json"})

    def _request(self, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}/api/v4{path}"
        resp = self.session.get(url, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _request_text(self, path: str, **kwargs: Any) -> str:
        url = f"{self.base_url}/api/v4{path}"
        resp = self.session.get(url, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.text

    def list_tree(self, docs_path: str) -> list[dict[str, Any]]:
        page = 1
        all_items: list[dict[str, Any]] = []
        while True:
            batch = self._request(
                f"/projects/{self.project_id}/repository/tree",
                params={
                    "path": docs_path,
                    "ref": self.ref,
                    "recursive": True,
                    "per_page": 100,
                    "page": page,
                },
            )
            if not batch:
                break
            all_items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return all_items

    def get_file_content(self, file_path: str) -> str:
        encoded = quote(file_path, safe="")
        return self._request_text(
            f"/projects/{self.project_id}/repository/files/{encoded}/raw",
            params={"ref": self.ref},
        )

    def get_file_bytes(self, file_path: str) -> bytes:
        encoded = quote(file_path, safe="")
        url = f"{self.base_url}/api/v4/projects/{self.project_id}/repository/files/{encoded}/raw"
        resp = self.session.get(url, timeout=60, params={"ref": self.ref})
        resp.raise_for_status()
        return resp.content

    def search_projects(self, query: str, per_page: int = 20) -> list[dict[str, str]]:
        payload = self._request(
            "/projects",
            params={"search": query, "simple": True, "per_page": max(1, min(per_page, 100))},
        )
        out: list[dict[str, str]] = []
        for item in payload:
            out.append(
                {
                    "id": str(item.get("id", "")),
                    "name": str(item.get("name", "")),
                    "path_with_namespace": str(item.get("path_with_namespace", "")),
                    "web_url": str(item.get("web_url", "")),
                }
            )
        return out


from __future__ import annotations

from pathlib import Path
import posixpath

from .gitlab_client import GitLabClient
from .models import SourceDocument, title_from_path


def load_local_markdown_docs(root: Path) -> list[SourceDocument]:
    if not root.exists():
        return []
    docs: list[SourceDocument] = []
    for path in root.rglob("*.md"):
        body = path.read_text(encoding="utf-8")
        docs.append(
            SourceDocument(
                title=title_from_path(str(path.relative_to(root))),
                body=body,
                source="local",
                path=str(path),
                relative_path=str(path.relative_to(root)),
            )
        )
    return sorted(docs, key=lambda d: d.relative_path.lower())


def load_gitlab_markdown_docs(client: GitLabClient, docs_path: str) -> list[SourceDocument]:
    files = client.list_tree(docs_path)
    docs: list[SourceDocument] = []
    for file_meta in files:
        if file_meta.get("type") != "blob":
            continue
        file_path = str(file_meta.get("path", ""))
        if not file_path.endswith(".md"):
            continue
        body = client.get_file_content(file_path)
        docs.append(
            SourceDocument(
                title=title_from_path(file_path),
                body=body,
                source="gitlab",
                path=file_path,
                relative_path=file_path,
            )
        )
    return sorted(docs, key=lambda d: d.relative_path.lower())


def read_local_asset_bytes(root: Path, doc: SourceDocument, link: str) -> bytes | None:
    doc_dir = Path(doc.relative_path).parent
    rel = (doc_dir / Path(link)).as_posix()
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root.resolve()):
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate.read_bytes()


def read_gitlab_asset_bytes(client: GitLabClient, doc: SourceDocument, link: str) -> bytes | None:
    doc_dir = posixpath.dirname(doc.relative_path.replace("\\", "/"))
    rel = posixpath.normpath(posixpath.join(doc_dir, link.replace("\\", "/")))
    try:
        return client.get_file_bytes(rel)
    except Exception:
        return None


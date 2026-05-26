from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceDocument:
    title: str
    body: str
    source: str
    path: str
    relative_path: str


def title_from_path(path: str) -> str:
    stem = Path(path).stem
    return stem.replace("_", " ").replace("-", " ").strip().title()


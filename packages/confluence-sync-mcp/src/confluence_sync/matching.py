from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from .models import SourceDocument

_TOKEN_RE = re.compile(r"[A-Za-z0-9\u0400-\u04FF_]+", flags=re.UNICODE)
_HEADING_RE = re.compile(r"^\s{0,3}#{1,3}\s+(.+?)\s*$", flags=re.MULTILINE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def _headings(markdown: str) -> list[str]:
    return [m.group(1).strip() for m in _HEADING_RE.finditer(markdown)]


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class MatchCandidate:
    doc_relative_path: str
    doc_title: str
    score: float
    reasons: list[str]


@dataclass(frozen=True)
class MatchDecision:
    selected_doc_path: str | None
    confidence: float
    ambiguous: bool
    candidates: list[MatchCandidate]
    message: str


def rank_documents_for_confluence_page(
    docs: list[SourceDocument],
    *,
    page_title: str,
    page_text: str,
    page_ancestors: list[str] | None = None,
) -> MatchDecision:
    if not docs:
        return MatchDecision(None, 0.0, True, [], "No markdown documents found.")

    page_tokens = _tokens(f"{page_title}\n{page_text}")
    page_heading_tokens = _tokens("\n".join(_headings(page_text)))
    ancestor_tokens = _tokens("/".join(page_ancestors or []))

    scored: list[MatchCandidate] = []
    for d in docs:
        doc_headings = _headings(d.body)
        doc_text_for_tokens = "\n".join([d.title, *doc_headings, d.body[:2000]])
        doc_tokens = _tokens(doc_text_for_tokens)
        doc_heading_tokens = _tokens("\n".join(doc_headings))
        path_tokens = _tokens(d.relative_path.replace("\\", "/"))

        title_sim = SequenceMatcher(None, page_title.lower(), d.title.lower()).ratio()
        token_sim = _jaccard(page_tokens, doc_tokens)
        heading_sim = _jaccard(page_heading_tokens, doc_heading_tokens)
        hierarchy_sim = _jaccard(ancestor_tokens, path_tokens)
        structural_sim = 1.0 - min(abs(len(doc_headings) - len(_headings(page_text))) / 20.0, 1.0)

        score = (
            0.35 * title_sim
            + 0.30 * token_sim
            + 0.20 * heading_sim
            + 0.10 * hierarchy_sim
            + 0.05 * structural_sim
        )
        reasons = [
            f"title={title_sim:.2f}",
            f"tokens={token_sim:.2f}",
            f"headings={heading_sim:.2f}",
            f"hierarchy={hierarchy_sim:.2f}",
        ]
        scored.append(
            MatchCandidate(
                doc_relative_path=d.relative_path,
                doc_title=d.title,
                score=round(score, 4),
                reasons=reasons,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    top = scored[0]
    second = scored[1] if len(scored) > 1 else None
    gap = top.score - (second.score if second else 0.0)
    ambiguous = top.score < 0.30 or gap < 0.08
    selected = None if ambiguous else top.doc_relative_path
    if ambiguous:
        message = (
            "Low-confidence markdown match for target Confluence page. "
            "Choose target markdown explicitly or pick one of candidates."
        )
    else:
        message = "High-confidence markdown match selected automatically."
    return MatchDecision(
        selected_doc_path=selected,
        confidence=top.score,
        ambiguous=ambiguous,
        candidates=scored[:5],
        message=message,
    )


def rank_documents_for_page_payload(
    docs: list[SourceDocument],
    page: dict[str, Any],
) -> MatchDecision:
    body = page.get("body", {})
    storage = body.get("storage", {}) if isinstance(body, dict) else {}
    page_text = str(storage.get("value", ""))[:10000]
    ancestors = [str(a.get("title", "")) for a in page.get("ancestors", []) if isinstance(a, dict)]
    return rank_documents_for_confluence_page(
        docs,
        page_title=str(page.get("title", "")),
        page_text=page_text,
        page_ancestors=ancestors,
    )

from __future__ import annotations

import re
from dataclasses import dataclass


_H_RE = re.compile(r"(<h([1-6])[^>]*>.*?</h\2>)", flags=re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_MACRO_RE = re.compile(r"<ac:structured-macro\b|<ac:adf-extension\b", flags=re.IGNORECASE)


def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text).strip().lower()


@dataclass(frozen=True)
class MergeResult:
    storage_html: str
    risk_score: float
    mode: str
    details: str


def merge_storage_preserving_style(existing_storage: str, new_storage: str) -> MergeResult:
    existing_heads = list(_H_RE.finditer(existing_storage))
    new_heads = list(_H_RE.finditer(new_storage))

    if not existing_heads or not new_heads:
        risk = 0.35 if _MACRO_RE.search(existing_storage) else 0.1
        return MergeResult(new_storage, risk, "replace", "No headings in one side; used full replace.")

    existing_titles = {_strip_tags(m.group(1)): m for m in existing_heads}
    shared = [_strip_tags(m.group(1)) for m in new_heads if _strip_tags(m.group(1)) in existing_titles]

    if not shared:
        risk = 0.55 if _MACRO_RE.search(existing_storage) else 0.25
        return MergeResult(new_storage, risk, "replace", "No shared headings; full replace.")

    # Lightweight section-level patch: keep prefix/suffix and replace shared heading sections.
    patched = existing_storage
    replacements = 0
    for i, nm in enumerate(new_heads):
        title = _strip_tags(nm.group(1))
        if title not in existing_titles:
            continue
        n_start = nm.start()
        n_end = new_heads[i + 1].start() if i + 1 < len(new_heads) else len(new_storage)
        new_section = new_storage[n_start:n_end]

        em = existing_titles[title]
        # locate section bounds in current patched snapshot
        # best-effort exact location by heading text
        heading_html = em.group(1)
        idx = patched.lower().find(heading_html.lower())
        if idx < 0:
            continue
        # find next heading after idx
        after = patched[idx + len(heading_html) :]
        nxt = _H_RE.search(after)
        old_end = (idx + len(heading_html) + nxt.start()) if nxt else len(patched)
        patched = patched[:idx] + new_section + patched[old_end:]
        replacements += 1

    coverage = replacements / max(len(new_heads), 1)
    risk = max(0.0, 0.5 - 0.35 * coverage)
    if _MACRO_RE.search(existing_storage):
        risk += 0.1
    return MergeResult(
        storage_html=patched,
        risk_score=round(min(risk, 1.0), 3),
        mode="section_patch",
        details=f"Patched {replacements}/{len(new_heads)} heading sections.",
    )

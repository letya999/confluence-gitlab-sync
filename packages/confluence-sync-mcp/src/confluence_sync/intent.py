from __future__ import annotations

import re

_RENAME_PATTERNS = [
    re.compile(r"\brename\b", flags=re.IGNORECASE),
    re.compile(r"\bretitle\b", flags=re.IGNORECASE),
    re.compile(r"\bchange\s+title\b", flags=re.IGNORECASE),
    re.compile(r"\bпереимен(овать|уй|уйте|ование)\b", flags=re.IGNORECASE),
    re.compile(r"\bсмен(ить|а)\s+названи", flags=re.IGNORECASE),
]


def extract_sync_meta_field(markdown_text: str, key: str) -> str:
    marker_start = "<!-- sync-meta:start -->"
    marker_end = "<!-- sync-meta:end -->"
    s = markdown_text.find(marker_start)
    e = markdown_text.find(marker_end)
    if s < 0 or e <= s:
        return ""
    block = markdown_text[s:e]
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().lower() == key.strip().lower():
            return v.strip()
    return ""


def wants_rename(*, user_intent_text: str, markdown_text: str, current_page_title: str) -> bool:
    if user_intent_text:
        for p in _RENAME_PATTERNS:
            if p.search(user_intent_text):
                return True
    desired = extract_sync_meta_field(markdown_text, "confluence_title")
    if desired and current_page_title and desired.strip() != current_page_title.strip():
        return True
    return False

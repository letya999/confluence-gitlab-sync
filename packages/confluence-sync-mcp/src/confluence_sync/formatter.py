from __future__ import annotations

import re
from html import unescape
from typing import cast

import markdown

_LIST_ITEM_RE = re.compile(r"(?:[-*+]\s+|\d+\.\s+)")
_CODE_BLOCK_RE = re.compile(
    r"<pre><code(?: class=\"(?P<class>[^\"]+)\")?>(?P<body>.*?)</code></pre>",
    flags=re.DOTALL,
)


def _is_list_item(line: str) -> bool:
    return bool(_LIST_ITEM_RE.match(line.strip()))


def _normalize_markdown_lists(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    normalized: list[str] = []
    in_fence = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence

        if (
            not in_fence
            and stripped
            and _is_list_item(stripped)
            and normalized
            and normalized[-1].strip()
            and normalized[-1].rstrip().endswith(":")
            and not _is_list_item(normalized[-1])
        ):
            normalized.append("")

        normalized.append(line)

    trailing_newline = "\n" if markdown_text.endswith("\n") else ""
    return "\n".join(normalized) + trailing_newline


def _macro_cdata(text: str) -> str:
    return text.replace("]]>", "]]]]><![CDATA[>")


def _build_code_macro(code: str, language: str = "") -> str:
    parts = ['<ac:structured-macro ac:name="code">']
    if language:
        parts.append(f'<ac:parameter ac:name="language">{language}</ac:parameter>')
    parts.append(f"<ac:plain-text-body><![CDATA[{_macro_cdata(code)}]]></ac:plain-text-body>")
    parts.append("</ac:structured-macro>")
    return "".join(parts)


def _replace_html_code_blocks(storage_html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        class_name = match.group("class") or ""
        language = ""
        if "language-" in class_name:
            language = class_name.split("language-", 1)[1].split()[0]
        code = unescape(match.group("body"))
        return _build_code_macro(code, language=language)

    return _CODE_BLOCK_RE.sub(repl, storage_html)


def markdown_to_confluence_storage(markdown_text: str) -> str:
    normalized_markdown = _normalize_markdown_lists(markdown_text)
    return cast(
        str,
        _replace_html_code_blocks(
            markdown.markdown(
                normalized_markdown,
                extensions=[
                    "fenced_code",
                    "tables",
                    "sane_lists",
                    "admonition",
                    "toc",
                ],
                output_format="xhtml",
            )
        ),
    )


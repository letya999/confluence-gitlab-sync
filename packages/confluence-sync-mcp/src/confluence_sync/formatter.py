from __future__ import annotations

from typing import cast

import markdown


def markdown_to_confluence_storage(markdown_text: str) -> str:
    return cast(
        str,
        markdown.markdown(
            markdown_text,
            extensions=[
                "fenced_code",
                "tables",
                "sane_lists",
                "admonition",
                "toc",
                "nl2br",
            ],
            output_format="xhtml",
        ),
    )


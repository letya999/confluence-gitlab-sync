from confluence_sync.formatter import markdown_to_confluence_storage


def test_markdown_to_storage_handles_table_and_code() -> None:
    md = """# Title

| a | b |
|---|---|
| 1 | 2 |

```python
print("x")
```
"""
    html = markdown_to_confluence_storage(md)
    assert "<h1" in html
    assert "<table" in html
    assert "<code" in html


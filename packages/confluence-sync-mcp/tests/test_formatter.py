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
    assert 'ac:name="code"' in html
    assert '<ac:parameter ac:name="language">python</ac:parameter>' in html


def test_markdown_to_storage_breaks_label_and_list_into_real_list() -> None:
    md = """## Section

Контракт результата:
- `preflight.is_executable_now`
- `preflight.warnings[]`
- `preflight.reasons[]`
"""
    html = markdown_to_confluence_storage(md)
    assert "<ul>" in html
    assert "<li><code>preflight.is_executable_now</code></li>" in html
    assert "Контракт результата:" in html


from confluence_sync.matching import rank_documents_for_confluence_page
from confluence_sync.models import SourceDocument


def _doc(title: str, body: str, rel: str) -> SourceDocument:
    return SourceDocument(title=title, body=body, source="local", path=rel, relative_path=rel)


def test_rank_documents_picks_best_when_confident() -> None:
    docs = [
        _doc("System Overview", "# System Overview\nbulk flow and point flow", "a.md"),
        _doc(
            "Бизнес Требования MQOS",
            "# Бизнес-требования MQOS\nМаркетолог и инструменты\n## Сценарии использования",
            "b.md",
        ),
    ]
    decision = rank_documents_for_confluence_page(
        docs,
        page_title="Бизнес-требования: Marketing Query Orchestration System (MQOS)",
        page_text="<h1>Бизнес-требования</h1><p>Маркетолог</p>",
        page_ancestors=["Architecture", "MQOS"],
    )
    assert decision.ambiguous is False
    assert decision.selected_doc_path == "b.md"


def test_rank_documents_reports_ambiguity() -> None:
    docs = [
        _doc("Doc A", "# Intro\nfoo", "a.md"),
        _doc("Doc B", "# Intro\nbar", "b.md"),
    ]
    decision = rank_documents_for_confluence_page(
        docs,
        page_title="Unknown",
        page_text="<p>random text</p>",
        page_ancestors=[],
    )
    assert decision.ambiguous is True
    assert decision.selected_doc_path is None
    assert len(decision.candidates) >= 2

from __future__ import annotations

from ..schemas.citation import Citation


def find_substring_span(source_text: str, text_quote: str) -> tuple[int | None, int | None]:
    if not source_text or not text_quote:
        return None, None
    start = source_text.find(text_quote)
    if start < 0:
        return None, None
    end = start + len(text_quote)
    return start, end


def validate_citation(citation: Citation) -> Citation:
    if citation.text_quote is None:
        citation.char_start = None
        citation.char_end = None
        return citation

    if citation.text_quote == "":
        citation.text_quote = None
        citation.char_start = None
        citation.char_end = None
        return citation

    if citation.char_start is not None and citation.char_end is not None:
        if 0 <= citation.char_start <= citation.char_end <= len(citation.source_text):
            exact = citation.source_text[citation.char_start : citation.char_end]
            if exact == citation.text_quote:
                return citation
        citation.char_start = None
        citation.char_end = None

    start, end = find_substring_span(citation.source_text, citation.text_quote)
    if start is None or end is None:
        citation.text_quote = None
        citation.char_start = None
        citation.char_end = None
        return citation

    citation.char_start = start
    citation.char_end = end
    if citation.source_text[start:end] != citation.text_quote:
        raise ValueError("Citation validation failed: text_quote mismatch")
    return citation


def normalize_citations(citations: list[Citation]) -> list[Citation]:
    normalized: list[Citation] = []
    for citation in citations:
        try:
            normalized.append(validate_citation(citation))
        except ValueError:
            citation.text_quote = None
            citation.char_start = None
            citation.char_end = None
            normalized.append(citation)
    return normalized


if __name__ == "__main__":
    sample = Citation(
        citation_id="c1",
        source_type="paper",
        source_id="p1",
        source_text="abc def ghi",
        text_quote="def",
        char_start=None,
        char_end=None,
    )
    print(normalize_citations([sample])[0].model_dump())

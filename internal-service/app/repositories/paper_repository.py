from __future__ import annotations

from ..schemas.input import PaperSummary

_MOCK_PAPERS: dict[str, PaperSummary] = {
    "paper-demo-001": PaperSummary(
        paper_id="paper-demo-001",
        title="Adaptive RAG for Domain Reports",
        summary_md=(
            "이 논문은 도메인 문서와 외부 문헌을 결합해 비교형 보고서를 생성하는 "
            "Adaptive RAG 프레임워크를 제안한다. "
            "핵심 기술은 요구사항 추출, 근거 정렬, 근거 기반 생성, 신뢰도 추정이다."
        ),
        paper_url="https://example.org/paper-demo-001",
        authors=["Jane Kim", "Min Park"],
        category="LLM Engineering",
    )
}


def get_paper_summary(paper_id: str) -> PaperSummary:
    if paper_id in _MOCK_PAPERS:
        return _MOCK_PAPERS[paper_id]

    return PaperSummary(
        paper_id=paper_id,
        title=f"Auto-generated paper for {paper_id}",
        summary_md=(
            "입력된 paper_id에 대한 사전 데이터가 없어 기본 논문 요약을 반환한다. "
            "요구사항-기술 매핑과 citation anchor 생성에 필요한 최소 정보를 포함한다."
        ),
        paper_url=f"https://example.org/{paper_id}",
        authors=["Unknown"],
        category="Unknown",
    )

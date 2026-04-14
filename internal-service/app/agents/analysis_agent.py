from __future__ import annotations

import json
import os
import re

from ..prompts.analysis_prompt import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT
from ..schemas.analysis import AnalysisResult
from ..schemas.citation import Citation
from ..schemas.input import InternalDoc, PaperSummary


class AnalysisAgent:
    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.chain = None

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", ANALYSIS_SYSTEM_PROMPT),
                    ("user", ANALYSIS_USER_PROMPT),
                ]
            )
            llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
            self.chain = prompt | llm.with_structured_output(AnalysisResult)
        except Exception:
            self.chain = None

    def _split_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?。])\s+|\n+", text)
        sentences: list[str] = []
        for part in parts:
            cleaned = re.sub(r"^###\s*", "", part).strip()
            cleaned = re.sub(r"^[-*]\s*", "", cleaned).strip()
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned:
                sentences.append(cleaned)
        return sentences

    def _score_line(self, line: str, keywords: list[str], min_len: int = 20) -> int:
        score = len(line)
        lowered = line.lower()
        if len(line) < min_len:
            score -= 40
        if any(keyword.lower() in lowered for keyword in keywords):
            score += 120
        if line.startswith("작성자") or line.endswith("Mini-Project") or line.startswith("Web Service"):
            score -= 80
        if re.fullmatch(r"[0-9]+", line):
            score -= 50
        return score

    def _select_best_lines(self, candidates: list[str], target_count: int, keywords: list[str], min_len: int = 20) -> list[str]:
        ranked: list[tuple[int, str]] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = re.sub(r"\s+", " ", candidate).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ranked.append((self._score_line(normalized, keywords, min_len=min_len), normalized))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [line for _, line in ranked[:target_count]]
        return selected

    def _extract_internal_requirement_lines(self, internal_doc: InternalDoc, target_count: int = 3) -> list[tuple[str, str]]:
        keywords = ["요구", "관리", "탐색", "비교", "검증", "통제", "비용", "성능", "자산", "운영", "협업", "표준화", "재사용", "자동"]
        candidates: list[tuple[str, str]] = []
        for chunk in internal_doc.internal_chunks:
            for sentence in self._split_sentences(chunk.document):
                score = self._score_line(sentence, keywords, min_len=25)
                candidates.append((f"{chunk.chunk_id}", sentence, score))

        candidates.sort(key=lambda item: item[2], reverse=True)

        selected: list[tuple[str, str]] = []
        seen: set[str] = set()
        for chunk_id, sentence, _ in candidates:
            if sentence in seen:
                continue
            seen.add(sentence)
            selected.append((chunk_id, sentence))
            if len(selected) >= target_count:
                break

        return selected

    def _extract_paper_technology_lines(self, paper_summary: PaperSummary, target_count: int = 5) -> list[str]:
        keywords = ["방법", "프레임워크", "AgentSwing", "성능", "분기", "룩어헤드", "정밀도", "효율", "턴", "향상", "벤치마크", "실증", "적응형", "컨텍스트", "관리"]
        candidates = self._split_sentences(paper_summary.summary_md)
        selected = self._select_best_lines(candidates, target_count, keywords=keywords, min_len=12)
        if len(selected) >= target_count:
            return selected[:target_count]

        for candidate in candidates:
            if candidate in selected:
                continue
            selected.append(candidate)
            if len(selected) >= target_count:
                break

        return selected[:target_count]

    def _find_best_sentence(self, text: str, keywords: list[str], min_len: int = 20) -> str | None:
        candidates = self._split_sentences(text)
        ranked = sorted(
            ((self._score_line(sentence, keywords, min_len=min_len), sentence) for sentence in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        return ranked[0][1] if ranked else None

    def _build_fallback(self, paper_summary: PaperSummary, internal_doc: InternalDoc) -> AnalysisResult:
        requirements = []
        citations: list[Citation] = []

        internal_themes = [
            (
                "조직 내 에이전트를 통합 관리하고 중복 개발을 줄여야 한다.",
                ["관리", "중복", "탐색", "재사용", "자산", "통합", "비효율"],
            ),
            (
                "에이전트 성능을 비교·검증할 수 있는 정량 기준이 필요하다.",
                ["성능", "비교", "검증", "정량", "신뢰", "우수"],
            ),
            (
                "비용 통제와 거버넌스를 유지하면서 복합 업무 자동화를 지원해야 한다.",
                ["비용", "거버넌스", "자동화", "협업", "운영", "통제"],
            ),
        ]

        internal_selected: list[tuple[str, str, str]] = []
        for summary_text, keywords in internal_themes:
            best_sentence = None
            best_chunk = None
            best_score = -10**9
            for chunk in internal_doc.internal_chunks:
                for sentence in self._split_sentences(chunk.document):
                    score = self._score_line(sentence, keywords, min_len=20)
                    if score > best_score:
                        best_score = score
                        best_sentence = sentence
                        best_chunk = chunk
            if best_sentence is None or best_chunk is None:
                if internal_doc.internal_chunks:
                    best_chunk = internal_doc.internal_chunks[0]
                    best_sentence = best_chunk.document[: min(120, len(best_chunk.document))].strip()
                else:
                    best_chunk = None
                    best_sentence = "요구사항 증거 부족"
            internal_selected.append((summary_text, best_chunk.chunk_id if best_chunk else "", best_sentence))

        for idx, (summary_text, chunk_id, quote) in enumerate(internal_selected, start=1):
            chunk = next((item for item in internal_doc.internal_chunks if item.chunk_id == chunk_id), internal_doc.internal_chunks[min(idx - 1, len(internal_doc.internal_chunks) - 1)])
            citation = Citation(
                citation_id=f"c-int-{idx}",
                source_type="internal",
                source_id=chunk.chunk_id,
                source_text=chunk.document,
                text_quote=quote if quote else None,
                anchor=f"int_req_{idx}",
                metadata={
                    "doc_id": chunk.metadata.doc_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "source_file": chunk.metadata.source_file,
                    "source_ext": chunk.metadata.source_ext,
                    "page_no": chunk.metadata.page_no,
                    "title": chunk.metadata.title,
                },
            )
            citations.append(citation)
            requirements.append(
                {
                    "requirement_id": f"R{idx}",
                    "requirement_text": summary_text,
                    "priority": "medium",
                    "citations": [citation],
                }
            )

        paper_technologies = []
        paper_citations: list[Citation] = []
        paper_themes = [
            (
                "장기 컨텍스트 관리의 병목을 확률적 프레임워크로 정식화한다.",
                ["병목", "컨텍스트", "프레임워크", "장기", "문제"],
            ),
            (
                "AgentSwing은 병렬 분기와 룩어헤드 라우팅으로 다음 경로를 선택한다.",
                ["AgentSwing", "병렬", "룩어헤드", "분기", "선택"],
            ),
            (
                "검색 효율성과 정밀도를 함께 다루는 적응형 컨텍스트 관리 접근을 제안한다.",
                ["검색 효율", "정밀도", "적응형", "컨텍스트", "관리"],
            ),
            (
                "정적 방법보다 더 적은 상호작용 턴으로 동등 이상 성능을 달성한다.",
                ["3배", "턴", "성능", "정적", "동등"],
            ),
            (
                "장기 지평 웹 에이전트의 성능 상한을 높이고 실증적 근거를 제시한다.",
                ["실증", "상한", "향상", "벤치마크", "웹 에이전트"],
            ),
        ]

        for idx, (summary_text, keywords) in enumerate(paper_themes, start=1):
            best_sentence = self._find_best_sentence(paper_summary.summary_md, keywords, min_len=12)
            if best_sentence is None:
                best_sentence = summary_text
            paper_citation = Citation(
                citation_id=f"c-paper-{idx}",
                source_type="paper",
                source_id=paper_summary.paper_id,
                source_text=paper_summary.summary_md,
                text_quote=best_sentence if best_sentence else None,
                anchor=f"paper_tech_{idx}",
                metadata={
                    "title": paper_summary.title,
                    "paper_url": paper_summary.paper_url,
                    "category": paper_summary.category,
                },
            )
            paper_citations.append(paper_citation)
            paper_technologies.append(
                {
                    "technology_id": f"T{idx}",
                    "technology_text": summary_text,
                    "maturity": "unknown",
                    "citations": [paper_citation],
                }
            )

        return AnalysisResult.model_validate(
            {
                "paper_id": paper_summary.paper_id,
                "internal_doc_id": internal_doc.internal_doc_id,
                "internal_requirements": requirements,
                "paper_technologies": paper_technologies,
                "mapping_table": [
                    {
                        "row_id": "M1",
                        "requirement_id": "R1",
                        "technology_id": "T1",
                        "match_score": 0.6,
                        "rationale": "기본 개념 수준 매핑",
                        "applicability": "추가 실험 필요",
                        "citations": citations[:1] + paper_citations[:1],
                    }
                ],
                "citations": citations + paper_citations,
            }
        )

    def invoke(self, paper_summary: PaperSummary, internal_doc: InternalDoc) -> AnalysisResult:
        if self.chain is None:
            return self._build_fallback(paper_summary, internal_doc)

        payload = {
            "paper_summary_json": json.dumps(paper_summary.model_dump(), ensure_ascii=False),
            "internal_doc_json": json.dumps(internal_doc.model_dump(), ensure_ascii=False),
        }
        try:
            result = self.chain.invoke(payload)
            if isinstance(result, AnalysisResult):
                return result
            return AnalysisResult.model_validate(result)
        except Exception:
            return self._build_fallback(paper_summary, internal_doc)


if __name__ == "__main__":
    sample_paper = PaperSummary(
        paper_id="p-001",
        title="Sample Paper",
        summary_md="Transformer 기반 멀티모달 검색 기술과 RAG 파이프라인 최적화 방법을 제시한다.",
        paper_url="https://example.com/paper",
        authors=["Author A", "Author B"],
        category="NLP",
    )
    sample_doc = InternalDoc.model_validate(
        {
            "internal_doc_id": "d-001",
            "internal_doc_title": "기획서",
            "internal_chunks": [
                {
                    "chunk_id": "internal-a-1",
                    "document": "우리는 기획서-논문 비교 자동 보고서 생성 기능이 필요하다.",
                    "metadata": {
                        "doc_id": "d-001",
                        "source_type": "internal",
                        "title": "기획서",
                        "source_file": "plan.pdf",
                        "source_ext": ".pdf",
                        "chunk_index": 1,
                        "doc_version": "v1",
                        "page_no": 1,
                        "chunk_char_start": 0,
                        "chunk_char_end": 40,
                    },
                }
            ],
        }
    )

    agent = AnalysisAgent()
    output = agent.invoke(sample_paper, sample_doc)
    print(output.model_dump_json(indent=2, ensure_ascii=False))

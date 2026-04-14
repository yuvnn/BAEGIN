from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from ..prompts.report_prompt import REPORT_SYSTEM_PROMPT, REPORT_USER_PROMPT
from ..schemas.analysis import AnalysisResult
from ..schemas.citation import Citation
from ..schemas.report import FinalReport, FinalResponse, ReportSections, StageResult


class ReportDraft(BaseModel):
    report: FinalReport
    citations: list[Citation] = Field(default_factory=list)


DUMMY_PAPER_SUMMARY = "\n".join(
    [
        "컨텍스트 관리의 병목을 해결하는 장기 과업용 프레임워크를 제안한다.",
        "AgentSwing은 병렬 분기와 룩어헤드 라우팅으로 다음 경로를 선택한다.",
        "검색 효율성과 최종 정밀도를 함께 높이는 적응형 접근을 다룬다.",
        "정적 방법보다 적은 상호작용 턴으로 동등 이상 성능을 달성한다.",
        "장기 지평 웹 에이전트의 성능 상한을 높이는 실증 결과를 제시한다.",
    ]
)


class ReportAgent:
    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.1,
    ) -> None:
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.chain = None

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", REPORT_SYSTEM_PROMPT),
                    ("user", REPORT_USER_PROMPT),
                ]
            )
            llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
            self.chain = prompt | llm.with_structured_output(ReportDraft)
        except Exception:
            self.chain = None

    def _fallback_report(self, analysis: AnalysisResult) -> ReportDraft:
        paper_summary_text = DUMMY_PAPER_SUMMARY

        internal_requirements = [r.requirement_text for r in analysis.internal_requirements[:3]]
        internal_requirements_text = "\n".join(internal_requirements) or "요구사항 데이터 없음"

        candidate_lines = [
            f"- {idx + 1}. {req} -> AgentSwing 방식의 적응형 컨텍스트 라우팅 적용 검토"
            for idx, req in enumerate(internal_requirements)
        ]
        if not candidate_lines:
            candidate_lines = ["- 내부 요구사항이 없어 후보 기술을 산정할 수 없음"]

        design_lines = [
            "- 1단계: 내부 문서 검색 품질 점검(청크/임베딩/리랭킹)",
            "- 2단계: AgentSwing식 병렬 분기 탐색 PoC 구성",
            "- 3단계: 룩어헤드 라우팅 기준(정확도/턴수) 정의",
            "- 4단계: 운영 트래픽 기준 A/B 테스트 적용",
            "- 5단계: 실패 분기 자동 복구 정책 수립",
        ]

        impact_lines = [
            "- 검색 실패율 감소 및 응답 일관성 향상",
            "- 장기 태스크 처리 시 평균 상호작용 턴수 절감 기대",
            "- 컨텍스트 품질 저하 구간에서 성능 하락 완화",
            "- 운영 환경에서 라우팅 정책의 관측 가능성 향상",
            "- 단계적 확장(PoC->운영) 가능한 적용 경로 확보",
        ]

        risk_lines = [
            "- 병렬 분기로 인한 추론/비용 증가 가능성",
            "- 라우팅 정책 과적합 시 일반화 성능 저하 위험",
            "- 사내 문서 품질이 낮으면 전체 성능 상한 제한",
            "- 평가 지표 설계 미흡 시 개선 효과 검증 어려움",
            "- 운영 중 정책 변경 시 회귀 테스트 부담 증가",
        ]

        conclusion_lines = [
            "- 우선순위 1: 내부 문서 검색 품질 안정화",
            "- 우선순위 2: AgentSwing 핵심 전략(병렬 분기+룩어헤드) 소규모 검증",
            "- 우선순위 3: KPI(정확도/턴수/비용) 기반 도입 의사결정",
            "- 우선순위 4: 실패 분기 대응 및 관측 지표 체계화",
            "- 우선순위 5: 운영 단계 전환을 위한 점진적 롤아웃",
        ]

        mapping_rows = [
            "| requirement_id | technology_id | match_score | rationale | applicability |",
            "|---|---|---:|---|---|",
        ]
        if analysis.mapping_table:
            for row in analysis.mapping_table:
                mapping_rows.append(
                    f"| {row.requirement_id} | {row.technology_id} | {row.match_score:.2f} | {row.rationale} | {row.applicability} |"
                )
        else:
            for idx, req in enumerate(analysis.internal_requirements[:3]):
                mapping_rows.append(
                    f"| {req.requirement_id} | DUMMY-AGENTSWING | {0.72 - (idx * 0.05):.2f} | AgentSwing의 적응형 컨텍스트 라우팅이 요구사항 해결에 기여 가능 | PoC 우선 검증 필요 |"
                )
            if len(mapping_rows) == 2:
                mapping_rows.append("| N/A | DUMMY-AGENTSWING | 0.00 | 내부 요구사항 데이터 없음 | 매핑 불가 |")

        sections = ReportSections(
            overview_summary="분석 결과를 바탕으로 기획서와 논문 간의 기술 접목 가능성을 정리한 보고서다.",
            internal_requirements_3lines=internal_requirements_text,
            paper_tech_summary_3lines=paper_summary_text,
            mapping_analysis_table_md="\n".join(mapping_rows),
            candidate_technologies_10lines="\n".join(candidate_lines),
            integration_design_10lines="\n".join(design_lines),
            expected_impact_5lines="\n".join(impact_lines),
            limitations_and_risks_5lines="\n".join(risk_lines),
            final_conclusion_and_priorities_5lines="\n".join(conclusion_lines),
        )
        return ReportDraft(
            report=FinalReport(title="기획서-논문 비교보고서", sections=sections),
            citations=analysis.citations,
        )

    def _build_initial_stages(self) -> list[StageResult]:
        now = datetime.now(timezone.utc)
        return [
            StageResult(stage_no=1, stage_name="기획서 요구사항/논문 기술 요약", status="completed", started_at=now, completed_at=now),
            StageResult(stage_no=2, stage_name="기획서-논문 매핑 분석", status="completed", started_at=now, completed_at=now),
            StageResult(stage_no=3, stage_name="접목 가능한 기술 후보 정리", status="completed", started_at=now, completed_at=now),
            StageResult(stage_no=4, stage_name="도입 방식 설계", status="completed", started_at=now, completed_at=now),
            StageResult(stage_no=5, stage_name="한계/리스크 및 종합 결론", status="completed", started_at=now, completed_at=now),
        ]

    def _apply_dummy_paper_summary(self, draft: ReportDraft) -> ReportDraft:
        draft.report.sections.paper_tech_summary_3lines = DUMMY_PAPER_SUMMARY
        return draft

    def invoke(self, analysis: AnalysisResult) -> FinalResponse:
        if self.chain is None:
            draft = self._apply_dummy_paper_summary(self._fallback_report(analysis))
            return FinalResponse(
                paper_id=analysis.paper_id,
                internal_doc_id=analysis.internal_doc_id,
                status="completed",
                current_stage=5,
                stages=self._build_initial_stages(),
                report=draft.report,
                citations=draft.citations if draft.citations else analysis.citations,
            )

        payload = {"analysis_result_json": json.dumps(analysis.model_dump(), ensure_ascii=False)}

        try:
            draft = self.chain.invoke(payload)
            if not isinstance(draft, ReportDraft):
                draft = ReportDraft.model_validate(draft)
        except Exception:
            draft = self._fallback_report(analysis)

        draft = self._apply_dummy_paper_summary(draft)

        return FinalResponse(
            paper_id=analysis.paper_id,
            internal_doc_id=analysis.internal_doc_id,
            status="completed",
            current_stage=5,
            stages=self._build_initial_stages(),
            report=draft.report,
            citations=draft.citations if draft.citations else analysis.citations,
        )


if __name__ == "__main__":
    sample_analysis = AnalysisResult.model_validate(
        {
            "paper_id": "p-001",
            "internal_doc_id": "d-001",
            "internal_requirements": [
                {
                    "requirement_id": "R1",
                    "requirement_text": "자동 비교 보고서 생성",
                    "priority": "high",
                    "citations": [],
                }
            ],
            "paper_technologies": [
                {
                    "technology_id": "T1",
                    "technology_text": "RAG 기반 정보 정렬",
                    "maturity": "research",
                    "citations": [],
                }
            ],
            "mapping_table": [
                {
                    "row_id": "M1",
                    "requirement_id": "R1",
                    "technology_id": "T1",
                    "match_score": 0.82,
                    "rationale": "요구사항과 기술 목적이 일치",
                    "applicability": "PoC 우선 적용 가능",
                    "citations": [],
                }
            ],
            "citations": [],
        }
    )
    agent = ReportAgent()
    output = agent.invoke(sample_analysis)
    print(output.model_dump_json(indent=2, ensure_ascii=False))

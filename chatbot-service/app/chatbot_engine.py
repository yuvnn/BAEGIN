import json
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class ChatbotEngine:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = model_name
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not set — chatbot will return fallback responses.")

    async def recommend(
        self,
        question: str,
        papers: list[dict],
        stats: dict | None = None,
        user_keywords: list[str] | None = None,
        internal_docs: list[dict] | None = None,
        reports: list[dict] | None = None,
    ) -> dict:
        """
        사용자 질문을 분석해 저장된 논문 중 관련성 높은 논문을 추천합니다.
        user_keywords가 있으면 개인화 추천을 우선합니다.
        internal_docs가 있으면 사내 문서 맥락도 반영합니다.
        """
        if self.client is None:
            return {
                "content": "OPENAI_API_KEY가 설정되지 않았습니다. 서버 환경변수를 확인하세요.",
                "recommended_papers": [],
            }

        stats = stats or {}
        user_keywords = user_keywords or []
        internal_docs = internal_docs or []
        reports = reports or []

        total = stats.get("total", len(papers))
        max_score = stats.get("max_score")
        avg_score = stats.get("avg_score")
        accepted_count = stats.get("accepted_count", 0)
        top_paper = stats.get("top_paper")

        stats_block = f"""[BAEGIN 논문 DB 현황]
- 총 저장 논문 수: {total}개
- AIRA Score 평균: {f"{avg_score:.1f}" if avg_score else "N/A"}
- AIRA Score 최고: {f"{max_score:.1f}" if max_score else "N/A"}
- Accept 논문 수 (≥ 5.0): {accepted_count}개
- 최고점 논문 ID: {top_paper["paper_id"] if top_paper else "N/A"} (점수: {f"{top_paper['aira_score']:.1f}" if top_paper and top_paper.get('aira_score') else "N/A"})
"""

        # 유저 관심 키워드 블록
        keywords_block = ""
        if user_keywords:
            kw_str = ", ".join(user_keywords)
            keywords_block = f"""
[사용자 관심 키워드]
{kw_str}
※ 사용자가 별도 요청 없이도 이 키워드와 관련된 논문을 우선 추천하세요.
  질문이 키워드와 무관한 일반 질문이라도, 답변 말미에 관심 키워드 관련 논문이 있다면 가볍게 언급하세요.
"""

        # 사내 문서 블록
        internal_block = ""
        if internal_docs:
            internal_block = f"""
[사내 문서 목록 (internal_docs 컬렉션)]
{json.dumps(internal_docs, ensure_ascii=False, indent=2)}
※ 사용자가 "사내 문서", "내부 문서", "프로젝트 문서" 등을 언급하면 이 목록을 참고해 답변하세요.
  사내 문서와 논문의 연관성을 설명할 수 있으면 적극 활용하세요.
"""

        # 비교 보고서 블록
        reports_block = ""
        if reports:
            completed = [r for r in reports if r.get("status") == "completed"]
            reports_block = f"""
[생성된 비교 보고서 목록 (report 테이블, 총 {len(reports)}개, 완료 {len(completed)}개)]
{json.dumps(reports, ensure_ascii=False, indent=2)}
※ 각 보고서는 특정 논문(paper_id)과 사내 문서(internal_doc_id)를 비교 분석한 결과입니다.
  보고서는 9개 섹션으로 구성됩니다:
  1. overview_summary (전체 요약)
  2. internal_requirements_3lines (사내 요구사항)
  3. paper_tech_summary_3lines (논문 기술 요약)
  4. mapping_analysis_table_md (기술 매핑 분석표)
  5. candidate_technologies_10lines (도입 후보 기술)
  6. integration_design_10lines (통합 설계 방안)
  7. expected_impact_5lines (기대 효과)
  8. limitations_and_risks_5lines (한계 및 리스크)
  9. final_conclusion_and_priorities_5lines (최종 결론 및 우선순위)
  사용자가 보고서 조회를 원하면 report_id를 안내하세요.
  새 보고서 생성은 paper_id와 internal_doc_id가 필요하다고 안내하세요.
"""

        system_prompt = (
            "당신은 BAEGIN 플랫폼의 AI 논문 도우미입니다. "
            "BAEGIN은 AI 논문을 자동으로 수집하고 'AIRA Score'(AI Research Assessment Score, 1.0~10.0)로 평가합니다. "
            "AIRA Score는 3인 심사 앙상블 + 1회 반성 루프 + Area Chair 메타리뷰로 산출되며, 5.0 이상이면 Accept입니다. "
            "BAEGIN은 논문 추천 외에도 논문과 사내 문서를 비교하는 '비교 보고서'를 자동 생성할 수 있습니다. "
            "사용자의 질문을 분석하여 논문 추천, 사내 문서 안내, 보고서 조회·생성 안내를 친절하고 간결한 한국어로 답변해주세요. "
            "사용자의 관심 키워드가 제공된 경우, 명시적 요청 없이도 그 키워드 관련 논문을 우선 추천하세요. "
            "반드시 유효한 JSON만 반환하세요. 다른 텍스트는 절대 포함하지 마세요."
        )

        user_prompt = f"""{stats_block}{keywords_block}{internal_block}{reports_block}
[저장된 논문 목록 (AIRA Score 높은 순, 최대 30개)]
{json.dumps(papers, ensure_ascii=False, indent=2)}

[사용자 질문]
{question}

[응답 지침]
1. 질문 의도를 파악하고 논문 목록에서 관련성 높은 논문의 paper_id를 선정하세요.
2. 사용자 관심 키워드가 있다면 해당 키워드와 관련된 논문을 우선 포함하세요.
3. "논문 몇 개", "총 몇 개" 등 개수 질문 → content에 총 저장 수({total}개)를 명시하고 recommended_papers는 비워두세요.
4. "가장 높은 점수", "최고 AIRA" 등 질문 → 최고점 논문을 recommended_papers에 포함하세요.
5. "사내 문서", "내부 문서" 관련 질문 → [사내 문서 목록]을 참고해 문서 제목과 doc_id를 content에 안내하세요.
6. "보고서", "비교 보고서" 관련 질문 → [생성된 비교 보고서 목록]을 참고해 report_id, 제목, 상태를 content에 안내하세요.
   새 보고서 생성을 원하면 "P3 화면에서 논문을 선택한 후 '보고서 생성' 버튼을 이용하세요"라고 안내하세요.
7. 관련 논문이 없으면 recommended_papers를 빈 배열로 반환하고 content에 안내하세요.
8. 논문 추천이 아닌 일반 질문(사용법, 기능 안내 등)은 content만 작성하고 recommended_papers는 비워두세요.
   단, 관심 키워드 관련 논문이 있다면 답변 끝에 1~2개 추가 추천해도 됩니다.

[응답 형식 - 이 JSON만 반환]
{{
    "content": "사용자에게 보여줄 친절한 한국어 설명 (2~4문장, 추천 이유 포함)",
    "recommended_papers": [
        {{
            "paper_id": "arxiv:xxxx.xxxxx",
            "category": "카테고리명",
            "reason": "이 논문을 추천하는 한 줄 이유"
        }}
    ]
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1000,
            )

            result = json.loads(response.choices[0].message.content)
            result.setdefault("content", "")
            result.setdefault("recommended_papers", [])
            return result

        except Exception as e:
            logger.error(f"ChatbotEngine error: {e}")
            return {
                "content": "죄송합니다. 추천 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "recommended_papers": [],
            }


chatbot_engine = ChatbotEngine()

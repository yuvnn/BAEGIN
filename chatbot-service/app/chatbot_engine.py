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

    async def recommend(self, question: str, papers: list[dict]) -> dict:
        """
        사용자 질문을 분석해 저장된 논문 중 관련성 높은 논문을 추천합니다.
        """
        if self.client is None:
            return {
                "content": "OPENAI_API_KEY가 설정되지 않았습니다. 서버 환경변수를 확인하세요.",
                "recommended_papers": [],
            }

        system_prompt = (
            "당신은 BAEGIN 플랫폼의 AI 논문 도우미입니다. "
            "사용자의 질문을 분석하여 저장된 논문 목록 중 가장 관련성 높은 논문들을 추천하고, "
            "친절하고 간결한 한국어로 답변해주세요. "
            "반드시 유효한 JSON만 반환하세요. 다른 텍스트는 절대 포함하지 마세요."
        )

        user_prompt = f"""[저장된 논문 목록]
{json.dumps(papers, ensure_ascii=False, indent=2)}

[사용자 질문]
{question}

[응답 지침]
1. 질문 의도를 파악하고 논문 목록에서 관련성 높은 논문의 paper_id를 선정하세요.
2. 관련 논문이 없으면 recommended_papers를 빈 배열로 반환하고 content에 안내하세요.
3. 논문 추천이 아닌 일반 질문(사용법, 기능 안내 등)은 content만 작성하고 recommended_papers는 비워두세요.

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
                max_tokens=800,
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

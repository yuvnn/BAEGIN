import os
import json
import logging
from openai import OpenAI
from typing import Dict, Any

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_for_prompt(text: str) -> str:
    """Escapes characters that might break the prompt or JSON structure."""
    if not text:
        return ""
    text = "".join(char for char in text if char.isprintable() or char in "\n\r\t")
    return text.replace('{', '(').replace('}', ')')


def summarize_paper(paper_id: str, title: str, abstract: str, body_text: str = "") -> Dict[str, Any]:
    """
    논문 전문을 분석하여 한국어로 상세한 요약본을 생성합니다.
    반환 형식은 PaperSummary 스키마를 준수하는 JSON입니다.
    """
    text_to_summarize = abstract
    if body_text:
        text_to_summarize = f"{abstract}\n\n{body_text}"

    max_chars = 15000
    clean_text = clean_for_prompt(text_to_summarize[:max_chars])

    prompt = f"""당신은 AI/ML 분야 전문 연구 분석가입니다. 아래 논문을 읽고 한국어로 상세한 요약 보고서를 작성하세요.

반드시 아래 JSON 스키마를 정확히 따르세요:
{{
  "paper_id": "{paper_id}",
  "title": "{title}",
  "summary": "아래 규칙에 따라 작성된 한국어 마크다운 요약 본문",
  "keywords": ["핵심 키워드1", "핵심 키워드2", ...],
  "citations": [
    {{ "text": "논문에서 인용할 만한 핵심 문장 (원문 영어 그대로)" }}
  ]
}}

[summary 작성 규칙]
- 반드시 **한국어**로 작성하세요.
- 마크다운 형식을 사용하세요 (##, ###, **굵게**, - 목록 등).
- 다음 섹션을 모두 포함하고 각 섹션을 충분히 상세하게 작성하세요:

  ### 문제 정의
  (논문이 해결하려는 문제와 그 중요성을 3~5문장으로 설명)

  ### 연구 방법론
  (제안된 방법, 알고리즘, 모델 구조를 구체적으로 설명. 핵심 아이디어를 bullet point로 정리)

  ### 주요 실험 결과
  (정량적 성능 수치, 비교 실험 결과를 포함하여 3~5문장으로 기술)

  ### 핵심 기여 및 의의
  (이 논문이 기존 연구 대비 무엇을 새롭게 기여하는지 bullet point로 정리)

  ### 한계점 및 향후 연구
  (논문이 언급하거나 추론 가능한 한계점과 향후 방향)

- 섹션 간 반드시 빈 줄(\\n\\n)을 삽입하세요.
- 최소 600자 이상 작성하세요.

[논문 내용]
제목: {title}
본문:
{clean_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 AI/ML 논문을 한국어로 분석하는 전문 연구 분석가입니다. "
                        "주어진 JSON 스키마를 정확히 따르고, summary 필드는 반드시 "
                        "한국어 마크다운으로 충분히 상세하게 작성하세요. "
                        "Output ONLY valid JSON."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result_str = response.choices[0].message.content.strip()
        if not result_str:
            raise ValueError("Empty response from OpenAI")

        result = json.loads(result_str)

        # 줄바꿈 보장: \\n이 literal로 저장된 경우 실제 \n으로 변환
        if "summary" in result and isinstance(result["summary"], str):
            result["summary"] = result["summary"].replace("\\n", "\n")

        return result

    except Exception as e:
        logger.error(f"Error summarizing paper '{title}': {e}")
        return {
            "paper_id": paper_id,
            "title": title,
            "summary": f"요약 생성 실패: {e}",
            "keywords": [],
            "citations": []
        }

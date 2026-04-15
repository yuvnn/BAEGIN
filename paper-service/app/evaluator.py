import os
import json
import logging
import re
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Assumes OPENAI_API_KEY is set in the environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EvaluationResult(BaseModel):
    is_relevant: bool
    score: float
    decision: str  # Accept, Weak Accept, Borderline, Weak Reject, Reject
    review: str    # Detailed meta-review or summary of the process

def clean_for_prompt(text: str) -> str:
    """Escapes characters that might break the prompt or JSON structure."""
    if not text:
        return ""
    # Ensure text doesn't contain weird characters that break LLM processing
    return text.replace('{', '(').replace('}', ')')

def generate_review_draft(keyword: str, title: str, text: str, temperature: float) -> Dict[str, Any]:
    """Generates an initial NeurIPS-style review draft."""
    clean_text = clean_for_prompt(text[:15000])
    prompt = f"""
    You are an expert AI researcher acting as a reviewer for a top-tier machine learning conference (e.g., NeurIPS).
    Evaluate the following paper based on its relevance to the keyword '{keyword}', methodology, and originality.
    
    CRUCIAL: The value of the paper must be proven by the authors. Focus on finding flaws and limitations.
    If the paper is completely unrelated to AI/ML (e.g., pure biology or finance without AI), it must be rejected.
    
    Title: {title}
    Text Content: {clean_text}
    
    Provide your evaluation in strict JSON format according to this rubric:
    1. Summary: Concise objective summary of contributions.
    2. Originality: Are the tasks or methods novel?
    3. Quality: Is the submission technically sound?
    4. Clarity: Is it well-organized and clearly written?
    5. Significance: Impact on the ML community.
    6. Questions to Authors: Specific questions to clarify doubts.
    7. Score: 1-10 scale (10: Top 5%, 8: Top 50%, 6: Marginally Accept, 4: Marginally Reject, 1: Trivial/Incorrect).
    
    JSON Schema:
    {{
        "summary": "string",
        "originality": "string",
        "quality": "string",
        "clarity": "string",
        "significance": "string",
        "questions": ["string"],
        "score": integer,
        "decision": "Accept" | "Weak Accept" | "Borderline" | "Weak Reject" | "Reject"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a critical academic reviewer. You focus on flaws and technical correctness. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error generating review draft: {e}")
        return {"score": 1, "decision": "Reject", "summary": f"Error: {e}"}

def reflect_on_review(title: str, text: str, current_review: Dict[str, Any]) -> Dict[str, Any]:
    """Models the self-reflection loop to improve review accuracy and critical depth."""
    review_json = json.dumps(current_review, indent=2)
    clean_text = clean_for_prompt(text[:5000])
    
    prompt = f"""
    You are a Meta-Reviewer reflecting on a generated review for the paper: {title}.
    
    Initial Review:
    {review_json}
    
    Tasks:
    1. Critically re-examine the paper's snippets: {clean_text}
    2. Does the initial review overestimate the results?
    3. Is the score justified by the identified weaknesses?
    4. Adjust the scores and qualitative analysis if they were too optimistic or missed a critical flaw.
    
    Output the updated review in the same JSON format.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a skeptical meta-reviewer. Ensure the review is not too lenient. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error in reflection loop: {e}")
        return current_review

def generate_meta_review(keyword: str, reviews: List[Dict[str, Any]]) -> EvaluationResult:
    """Acts as an Area Chair to synthesize independent ensemble reviews."""
    reviews_json = json.dumps(reviews, indent=2)
    prompt = f"""
    You are an Area Chair for a top-tier AI conference. You have independent reviews for a submission.
    Your task is to synthesize these reviews and make a final consensus decision.
    
    Conference Context: Topic '{keyword}'
    
    Committee Reviews:
    {reviews_json}
    
    Synthesize the consensus. If reviewers are split, lean towards the more critical and well-reasoned arguments.
    Provide a final JSON decision:
    {{
        "meta_review": "string (summarizing consensus and reasoning)",
        "final_score": float (1.0 to 10.0),
        "final_decision": "Accept" | "Weak Accept" | "Borderline" | "Weak Reject" | "Reject"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an Area Chair making a final decision based on committee reviews. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(response.choices[0].message.content)
        
        final_score = result.get("final_score", 0.0)
        accept = final_score >= 5.0

        final_decision = result.get("final_decision", "Reject")
        if final_decision == "Borderline":
            final_decision = "Weak Accept" if final_score >= 5.0 else "Weak Reject"

        return EvaluationResult(
            is_relevant=accept,
            score=final_score,
            decision=final_decision,
            review=result.get("meta_review", "No meta-review generated.")
        )
    except Exception as e:
        logger.error(f"Error generating meta-review: {e}")
        return EvaluationResult(is_relevant=False, score=0.0, decision="Reject", review=f"Meta-review failed: {e}")

def quick_relevance_check(keyword: str, title: str, abstract: str) -> bool:
    """
    gpt-4o-mini로 abstract만 보고 빠르게 관련성을 판단합니다 (Desk Rejection).

    명백히 AI/ML과 무관한 논문만 차단합니다. 판단이 애매하면 True(통과)를 반환하여
    이후 앙상블 평가에서 정밀하게 판단하도록 넘깁니다.
    오류 발생 시에도 True를 반환하여 파이프라인을 중단하지 않습니다.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a program chair doing desk rejection. "
                        "Be lenient — only reject papers that are completely unrelated to AI/ML research. "
                        "When in doubt, reply YES."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Is this paper relevant to AI/ML research and the topic '{keyword}'?\n\n"
                        f"Title: {title}\n"
                        f"Abstract: {abstract[:1000]}\n\n"
                        "Reply only YES or NO."
                    )
                }
            ],
            max_tokens=5,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().upper()
        return "NO" not in answer
    except Exception as e:
        logger.warning(f"Pre-filter check failed, defaulting to proceed: {e}")
        return True


def evaluate_paper(keyword: str, title: str, abstract: str, full_text: str = "") -> EvaluationResult:
    """
    Complete AI Scientist evaluation pipeline (Optimized for performance):
    1. Ensemble of 3 independent reviews (Reduced from 5 for speed).
    2. Each review undergoes 1 reflection loop (gpt-4o model quality preserved).
    3. Meta-review (Area Chair) synthesis.
    """
    num_ensemble = 3
    num_reflections = 1
    
    # Use full text if available, otherwise fallback to abstract
    content_to_review = full_text if full_text else abstract
    
    ensemble_reviews = []
    
    for i in range(num_ensemble):
        logger.info(f"Generating ensemble review {i+1}/{num_ensemble}...")
        review = generate_review_draft(keyword, title, content_to_review, temperature=0.1)
        
        for r in range(num_reflections):
            logger.info(f"  Reflection loop {r+1}/{num_reflections} for review {i+1}...")
            review = reflect_on_review(title, content_to_review, review)
            
        ensemble_reviews.append(review)
        
    return generate_meta_review(keyword, ensemble_reviews)

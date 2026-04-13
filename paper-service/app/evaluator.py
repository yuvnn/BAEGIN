import os
import json
import logging
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

def generate_review_draft(keyword: str, title: str, text: str, temperature: float) -> Dict[str, Any]:
    """Generates an initial NeurIPS-style review draft."""
    prompt = f"""
    You are an expert AI researcher acting as a reviewer for a top-tier machine learning conference (e.g., NeurIPS).
    Evaluate the following paper based on its relevance to the keyword '{keyword}', methodology, and originality.
    
    CRUCIAL: The value of the paper must be proven by the authors. Focus on finding flaws and limitations.
    If the paper is completely unrelated to AI/ML (e.g., pure biology or finance without AI), it must be rejected.
    
    Title: {title}
    Text: {text[:15000]}  # Limiting context for prompt efficiency
    
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
                {"role": "system", "content": "You are a critical academic reviewer. You focus on flaws and technical correctness."},
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
    prompt = f"""
    You are a Meta-Reviewer reflecting on a generated review for the paper: {title}.
    
    Initial Review:
    {review_json}
    
    Tasks:
    1. Critically re-examine the paper's text if provided: {text[:5000]}...
    2. Does the initial review overestimate the results?
    3. Is the score justified by the identified weaknesses?
    4. Adjust the scores and qualitative analysis if they were too optimistic or missed a critical flaw.
    
    Output the updated review in the same JSON format.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a skeptical meta-reviewer. Your job is to ensure the review is not too lenient."},
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
    """Acts as an Area Chair to synthesize 5 independent ensemble reviews."""
    reviews_json = json.dumps(reviews, indent=2)
    prompt = f"""
    You are an Area Chair for a top-tier AI conference. You have 5 independent reviews for a submission.
    Your task is to synthesize these reviews and make a final consensus decision.
    
    Conference Context: Topic '{keyword}'
    
    Reviews:
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
                {"role": "system", "content": "You are an Area Chair making a final decision based on committee reviews."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(response.choices[0].message.content)
        
        # Acceptance threshold is typically >= 6.0
        final_score = result.get("final_score", 0.0)
        accept = final_score >= 6.0
        
        return EvaluationResult(
            is_relevant=accept,
            score=final_score,
            decision=result.get("final_decision", "Reject"),
            review=result.get("meta_review", "No meta-review generated.")
        )
    except Exception as e:
        logger.error(f"Error generating meta-review: {e}")
        return EvaluationResult(is_relevant=False, score=0.0, decision="Reject", review=f"Meta-review failed: {e}")

def evaluate_paper(keyword: str, title: str, abstract: str, full_text: str = "") -> EvaluationResult:
    """
    Complete AI Scientist evaluation pipeline:
    1. Ensemble of 5 independent reviews.
    2. Each review undergoes 5 reflection loops.
    3. Meta-review (Area Chair) synthesis.
    """
    num_ensemble = 5
    num_reflections = 5
    
    # Use full text if available, otherwise fallback to abstract
    content_to_review = full_text if full_text else abstract
    
    ensemble_reviews = []
    
    for i in range(num_ensemble):
        logger.info(f"Generating ensemble review {i+1}/{num_ensemble}...")
        # Use low temperature for consistency as per doc
        review = generate_review_draft(keyword, title, content_to_review, temperature=0.1)
        
        # Reflection loops
        for r in range(num_reflections):
            logger.info(f"  Reflection loop {r+1}/{num_reflections} for review {i+1}...")
            review = reflect_on_review(title, content_to_review, review)
            
        ensemble_reviews.append(review)
        
    return generate_meta_review(keyword, ensemble_reviews)

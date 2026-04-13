import os
import json
import logging
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Assumes OPENAI_API_KEY is set in the environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EvaluationResult(BaseModel):
    is_relevant: bool
    score: float
    review: str

def evaluate_paper(keyword: str, title: str, abstract: str) -> EvaluationResult:
    """
    Evaluates a paper based on AI Scientist's Automated Reviewer approach.
    It scores the paper on relevance to the keyword, methodology, and originality.
    Returns whether the paper should be filtered in (score >= threshold).
    """
    prompt = f"""
    You are an expert AI researcher acting as an automated reviewer.
    Evaluate the following paper based on its relevance to the keyword '{keyword}', methodology, and originality.
    
    Title: {title}
    Abstract: {abstract}
    
    Provide your evaluation in JSON format exactly matching this schema:
    {{
        "score": float (1.0 to 10.0),
        "review": string (A brief explanation of the score and evaluation),
        "is_relevant": boolean (true if score >= 6.0, false otherwise)
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        
        result_str = response.choices[0].message.content
        if not result_str:
            raise ValueError("Empty response from OpenAI")
            
        result_dict = json.loads(result_str)
        return EvaluationResult(**result_dict)
        
    except Exception as e:
        logger.error(f"Error evaluating paper '{title}': {e}")
        # Default to rejecting if evaluation fails to be safe
        return EvaluationResult(is_relevant=False, score=0.0, review=f"Evaluation failed: {e}")

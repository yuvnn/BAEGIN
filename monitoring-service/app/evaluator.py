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
    review: str

def generate_individual_review(keyword: str, title: str, abstract: str, temperature: float) -> Dict[str, Any]:
    """Generates an independent review following NeurIPS style guidelines."""
    prompt = f"""
    You are an expert AI researcher acting as a reviewer for a top-tier machine learning conference.
    Evaluate the following paper based on its relevance to the keyword '{keyword}', methodology, and originality.
    
    Title: {title}
    Abstract: {abstract}
    
    Provide a structured review in JSON format matching this schema exactly:
    {{
        "summary": string (A concise summary of the paper's claimed contributions),
        "strengths": [string] (List of strengths),
        "weaknesses": [string] (List of weaknesses),
        "score": integer (1 to 10 scale, where 1 is strong reject and 10 is strong accept),
        "confidence": integer (1 to 5 scale, your confidence in this review)
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert academic reviewer designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        
        result_str = response.choices[0].message.content
        if not result_str:
            raise ValueError("Empty response from OpenAI")
            
        return json.loads(result_str)
    except Exception as e:
        logger.error(f"Error generating individual review: {e}")
        return {"summary": "Error", "strengths": [], "weaknesses": [], "score": 0, "confidence": 1}

def generate_meta_review(keyword: str, title: str, abstract: str, reviews: List[Dict[str, Any]]) -> EvaluationResult:
    """Acts as an Area Chair to synthesize independent reviews and make a final decision."""
    reviews_json = json.dumps(reviews, indent=2)
    
    prompt = f"""
    You are an Area Chair for a top-tier AI conference. You need to make a final decision on the following paper.
    Your goal is to decide if it is highly relevant to the topic '{keyword}' and meets the quality bar.
    
    Title: {title}
    Abstract: {abstract}
    
    Here are the 5 independent reviews from your committee:
    {reviews_json}
    
    Synthesize these reviews and provide your final decision in JSON format exactly matching this schema:
    {{
        "meta_review": string (A comprehensive meta-review summarizing the consensus and your reasoning),
        "final_score": float (The consensus score, usually a weighted average of reviewer scores, 1.0 to 10.0),
        "accept": boolean (true if final_score >= 6.0, false otherwise)
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an Area Chair designed to output JSON decisions."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        result_str = response.choices[0].message.content
        if not result_str:
            raise ValueError("Empty response from OpenAI Meta-Reviewer")
            
        result_dict = json.loads(result_str)
        return EvaluationResult(
            is_relevant=result_dict.get("accept", False),
            score=result_dict.get("final_score", 0.0),
            review=result_dict.get("meta_review", "No review provided")
        )
        
    except Exception as e:
        logger.error(f"Error generating meta review: {e}")
        return EvaluationResult(is_relevant=False, score=0.0, review=f"Meta evaluation failed: {e}")

def evaluate_paper(keyword: str, title: str, abstract: str) -> EvaluationResult:
    """
    Evaluates a paper using the AI Scientist Automated Reviewer ensemble method.
    1. Generates 5 independent reviews with varying temperatures.
    2. Uses a meta-reviewer (Area Chair) to synthesize and make a final decision.
    """
    # Temperatures for the 5 independent reviewers to ensure diverse perspectives
    temperatures = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    reviews = []
    for temp in temperatures:
        review = generate_individual_review(keyword, title, abstract, temp)
        # Skip failed reviews if any
        if review.get("score", 0) > 0:
            reviews.append(review)
            
    if not reviews:
        return EvaluationResult(is_relevant=False, score=0.0, review="All individual reviews failed.")
        
    return generate_meta_review(keyword, title, abstract, reviews)

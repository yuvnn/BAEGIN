import os
import json
import logging
from openai import OpenAI
from typing import Dict, Any

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_paper(paper_id: str, title: str, abstract: str, body_text: str = "") -> Dict[str, Any]:
    """
    Generates a concise summary of the paper and formats it according to the PaperSummary schema.
    """
    text_to_summarize = abstract
    if body_text:
        text_to_summarize = f"{abstract}\n\n{body_text}"
        
    # Truncate text to avoid hitting token limits for extremely long papers
    max_chars = 15000
    if len(text_to_summarize) > max_chars:
        text_to_summarize = text_to_summarize[:max_chars] + "... [truncated]"

    prompt = f"""
    Please provide a comprehensive yet concise summary of the following paper.
    You must return a JSON object matching this schema exactly:
    {{
      "paper_id": "{paper_id}",
      "title": "{title}",
      "summary": "The concise summary text covering problem, methodology, and findings. YOU MUST USE MARKDOWN FORMATTING HERE (e.g. headers, bullet points, bold text) for readability.",
      "keywords": ["keyword1", "keyword2", ...],
      "citations": [
        {{ "text": "Important quote from the paper" }}
      ]
    }}
    
    Title: {title}
    Text: {text_to_summarize}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly skilled research assistant that summarizes academic papers into strict JSON. You format your summaries beautifully using Markdown."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        
        result_str = response.choices[0].message.content.strip()
        if not result_str:
            raise ValueError("Empty response from OpenAI")
            
        return json.loads(result_str)
    except Exception as e:
        logger.error(f"Error summarizing paper '{title}': {e}")
        return {
            "paper_id": paper_id,
            "title": title,
            "summary": f"Summary generation failed: {e}",
            "keywords": [],
            "citations": []
        }

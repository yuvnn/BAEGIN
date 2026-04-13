import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_paper(title: str, abstract: str, body_text: str = "") -> str:
    """
    Generates a concise summary of the paper suitable for vector DB storage and human reading.
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
    The summary should cover:
    1. The core problem being solved
    2. The proposed methodology or approach
    3. The main findings or contributions
    
    Title: {title}
    Text: {text_to_summarize}
    
    Summary:
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly skilled research assistant that summarizes academic papers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error summarizing paper '{title}': {e}")
        return f"Summary generation failed: {e}"

import os
import requests
import tempfile
import logging
import re
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def sanitize_text(text: str) -> str:
    """
    Removes non-printable and potential JSON-breaking characters.
    """
    # Remove null bytes and other non-printable characters
    text = "".join(char for i, char in enumerate(text) if char.isprintable() or char in "\n\r\t")
    # Replace multiple newlines/spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def download_and_parse_pdf(pdf_url: str) -> str:
    """
    Downloads a PDF from the given URL and extracts its text.
    """
    try:
        logger.info(f"Downloading PDF from {pdf_url}")
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            for chunk in response.iter_content(chunk_size=8192):
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
            
        logger.info(f"PDF downloaded to {temp_pdf_path}. Parsing text...")
        text = ""
        with open(temp_pdf_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    
        # Cleanup
        os.remove(temp_pdf_path)
        
        # Sanitize before returning
        sanitized_text = sanitize_text(text)
        logger.info(f"PDF parsing complete. Sanitized text length: {len(sanitized_text)}")
        return sanitized_text
    except Exception as e:
        logger.error(f"Failed to download or parse PDF from {pdf_url}: {e}")
        return ""

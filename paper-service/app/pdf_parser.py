import os
import requests
import tempfile
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

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
        logger.info("PDF parsing complete.")
        return text
    except Exception as e:
        logger.error(f"Failed to download or parse PDF from {pdf_url}: {e}")
        return ""

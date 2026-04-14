import os
import requests
import tempfile
import logging
import pymupdf4llm

logger = logging.getLogger(__name__)


def download_and_parse_pdf(pdf_url: str) -> str:
    """
    PDF URL에서 파일을 다운로드하고 Markdown 형식의 텍스트를 반환합니다.

    pymupdf4llm을 사용하여 2단 레이아웃, 표, 수식 등을 포함한
    학술 논문 구조를 Markdown으로 정확하게 추출합니다.
    """
    try:
        logger.info(f"Downloading PDF from {pdf_url}")
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            for chunk in response.iter_content(chunk_size=8192):
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name

        logger.info(f"PDF downloaded to {temp_pdf_path}. Parsing to Markdown...")
        md_text = pymupdf4llm.to_markdown(temp_pdf_path)
        os.remove(temp_pdf_path)

        logger.info(f"PDF parsing complete. Markdown text length: {len(md_text)}")
        return md_text

    except Exception as e:
        logger.error(f"Failed to download or parse PDF from {pdf_url}: {e}")
        return ""

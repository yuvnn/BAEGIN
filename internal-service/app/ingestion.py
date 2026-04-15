import logging
from typing import Any

from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("all-MiniLM-L6-v2")
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 700) -> list[str]:
    chunks: list[str] = []
    buffer = []
    current_len = 0
    filtered_count = 0

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # pymupdf4llm이 이미지를 변환하는 placeholder — 형식 변동에 강건하게 문자열 포함 여부로 판단
        if "intentionally omitted" in paragraph:
            filtered_count += 1
            continue
        if current_len + len(paragraph) > chunk_size and buffer:
            chunks.append("\n".join(buffer))
            buffer = [paragraph]
            current_len = len(paragraph)
        else:
            buffer.append(paragraph)
            current_len += len(paragraph)

    if buffer:
        chunks.append("\n".join(buffer))

    if filtered_count:
        logger.info("[chunk_text] 이미지 placeholder %d개 제거됨", filtered_count)

    return chunks


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    vectors = MODEL.encode(chunks, normalize_embeddings=True)
    return vectors.tolist()


def build_metadata(doc_id: str, source_type: str, title: str) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "source_type": source_type,
        "title": title,
    }

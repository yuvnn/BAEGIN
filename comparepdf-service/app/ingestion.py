from typing import Any

from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, chunk_size: int = 700) -> list[str]:
    chunks: list[str] = []
    buffer = []
    current_len = 0

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
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

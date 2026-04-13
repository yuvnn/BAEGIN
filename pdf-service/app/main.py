import os

from fastapi import FastAPI
from pydantic import BaseModel

from .chroma_client import ensure_collections, get_chroma_client
from .ingestion import build_metadata, chunk_text, embed_chunks

app = FastAPI(title="pdf-service", version="0.1.0")


class IngestRequest(BaseModel):
    doc_id: str
    title: str
    text: str


@app.on_event("startup")
def startup() -> None:
    ensure_collections()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "pdf-service"}


@app.post("/ingest/internal")
def ingest_internal(payload: IngestRequest) -> dict:
    chunks = chunk_text(payload.text)
    embeddings = embed_chunks(chunks)
    metadata = build_metadata(payload.doc_id, "internal", payload.title)

    client = get_chroma_client()
    collection = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs"))

    ids = [f"{payload.doc_id}-{idx}" for idx in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[metadata for _ in chunks],
    )
    return {"ingested": len(chunks), "collection": "internal_docs"}


@app.post("/ingest/paper")
def ingest_paper(payload: IngestRequest) -> dict:
    chunks = chunk_text(payload.text)
    embeddings = embed_chunks(chunks)
    metadata = build_metadata(payload.doc_id, "paper", payload.title)

    client = get_chroma_client()
    collection = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_PAPERS", "papers"))

    ids = [f"{payload.doc_id}-{idx}" for idx in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[metadata for _ in chunks],
    )
    return {"ingested": len(chunks), "collection": "papers"}

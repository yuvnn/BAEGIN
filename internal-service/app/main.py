import os
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .api.report_routes import router as report_router
from .chroma_client import ensure_collections, get_chroma_client
from .database import engine, Base
from .ingestion import build_metadata, chunk_text, embed_chunks

app = FastAPI(title="internal-service", version="0.1.0")
app.include_router(report_router)


def _resolve_internal_docs_dir() -> Path:
    current = Path(__file__).resolve()
    app_root = current.parents[1]
    workspace_root = current.parents[2] if len(current.parents) > 2 else app_root
    candidates = [
        app_root.parent / "data" / "internal_docs",
        workspace_root / "data" / "internal_docs",
        Path("/data/internal_docs"),
        Path("/app/data/internal_docs"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return candidates[0]


INTERNAL_DOCS_DIR = _resolve_internal_docs_dir()
INTERNAL_DOC_FILE_MAP = {
    "internal-b482da9a0b960bde": "Web_Service_개발_Mini-Project.pdf",
}


class IngestRequest(BaseModel):
    doc_id: str
    title: str
    text: str


def _seed_internal_doc_if_missing() -> None:
    """Ensure the default internal document id exists for end-to-end report tests."""
    target_doc_id = "internal-b482da9a0b960bde"
    client = get_chroma_client()
    collection = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs"))

    existing = collection.get(where={"doc_id": target_doc_id}, include=[])
    if existing.get("ids"):
        return

    default_title = "Web_Service_개발_Mini-Project"
    source_file = INTERNAL_DOCS_DIR / INTERNAL_DOC_FILE_MAP[target_doc_id]
    if source_file.exists() and source_file.is_file():
        seed_text = (
            f"Internal source file detected: {source_file.name}. "
            "Use this document as internal requirement context for feasibility mapping and report generation."
        )
    else:
        seed_text = (
            "Internal requirements for BAEGIN project. "
            "This seeded fallback content exists to keep report pipeline testable when source PDF is unavailable. "
            "Focus on architecture constraints, integration design, expected impact, and risk analysis."
        )

    chunks = chunk_text(seed_text)
    embeddings = embed_chunks(chunks)
    metadata = build_metadata(target_doc_id, "internal", default_title)
    ids = [f"{target_doc_id}-{idx}" for idx in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[metadata for _ in chunks],
    )


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_collections()
    _seed_internal_doc_if_missing()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "internal-service"}


@app.get("/assets/internal-docs/{file_name}")
def get_internal_doc_file(file_name: str):
    safe_name = Path(file_name).name
    file_path = INTERNAL_DOCS_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Internal PDF not found: {safe_name}")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@app.get("/assets/internal-docs/by-doc/{doc_id}")
def get_internal_doc_by_id(doc_id: str):
    mapped = INTERNAL_DOC_FILE_MAP.get(doc_id)
    if mapped:
        safe_name = Path(mapped).name
        file_path = INTERNAL_DOCS_DIR / safe_name
        if file_path.exists() and file_path.is_file():
            return FileResponse(
                path=str(file_path),
                media_type="application/pdf",
                headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
            )

    pdf_files = sorted(INTERNAL_DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        fallback_name = INTERNAL_DOC_FILE_MAP.get("internal-b482da9a0b960bde")
        if fallback_name:
            fallback_path = INTERNAL_DOCS_DIR / Path(fallback_name).name
            if fallback_path.exists() and fallback_path.is_file():
                return FileResponse(
                    path=str(fallback_path),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{fallback_path.name}"'},
                )

    if len(pdf_files) == 1:
        picked = pdf_files[0]
        return FileResponse(
            path=str(picked),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{picked.name}"'},
        )

    raise HTTPException(status_code=404, detail=f"Internal PDF not found for doc_id: {doc_id}")


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

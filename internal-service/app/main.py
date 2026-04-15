import hashlib
import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import pymupdf4llm
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .api.report_routes import router as report_router
from .chroma_client import ensure_collections, get_chroma_client
from .database import SessionLocal, engine, Base
from .ingestion import build_metadata, chunk_text, embed_chunks
from .models import InternalDocument
from .repositories.internal_doc_repository import get_internal_doc as _get_internal_doc_from_chroma

logger = logging.getLogger(__name__)

app = FastAPI(title="internal-service", version="0.1.0")
app.include_router(report_router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


# ── PDF 파싱 헬퍼 ──────────────────────────────────────────────
def _extract_pdf_text(file_bytes: bytes, filename: str) -> str:
    """pymupdf4llm으로 PDF → Markdown 텍스트 추출."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        md_text = pymupdf4llm.to_markdown(tmp_path)
        return md_text or ""
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── ChromaDB 인제스트 헬퍼 ─────────────────────────────────────
def _ingest_doc_to_chroma(doc_id: str, title: str, text: str, source_file: str = "") -> int:
    """텍스트를 청킹·임베딩 후 ChromaDB internal_docs 저장. 청크 수 반환."""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embeddings = embed_chunks(chunks)
    meta = build_metadata(doc_id, "internal", title)
    if source_file:
        meta["source_file"] = source_file
    ids = [f"{doc_id}-{idx}" for idx in range(len(chunks))]

    col = get_chroma_client().get_or_create_collection(
        os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs")
    )
    try:
        col.delete(where={"doc_id": doc_id})
    except Exception:
        pass
    col.add(ids=ids, documents=chunks, embeddings=embeddings,
            metadatas=[meta for _ in chunks])
    return len(chunks)


# ── DB upsert 헬퍼 ─────────────────────────────────────────────
def _upsert_internal_doc_db(db: Session, doc_id: str, title: str, text: str,
                             source_file: str, chunk_count: int) -> None:
    doc = db.query(InternalDocument).filter_by(doc_id=doc_id).first()
    if doc:
        doc.title = title
        doc.original_text = text
        doc.source_file = source_file
        doc.chunk_count = chunk_count
        doc.created_at = datetime.utcnow()
    else:
        db.add(InternalDocument(
            doc_id=doc_id, title=title, original_text=text,
            source_file=source_file, chunk_count=chunk_count,
            created_at=datetime.utcnow(),
        ))
    db.commit()


# ── startup seeding ────────────────────────────────────────────
def _seed_internal_docs_from_dir() -> None:
    """INTERNAL_DOCS_DIR 내 모든 PDF를 자동 시딩 (파일명 → title, 해시 → doc_id)."""
    pdf_files = list(INTERNAL_DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        return

    col = get_chroma_client().get_or_create_collection(
        os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs")
    )
    db = SessionLocal()
    try:
        for pdf_path in pdf_files:
            doc_id = "internal-" + hashlib.md5(pdf_path.name.encode()).hexdigest()[:16]
            title = pdf_path.stem.replace("_", " ").replace("-", " ")

            existing = col.get(where={"doc_id": doc_id}, include=[])
            if existing.get("ids"):
                continue

            try:
                text = pymupdf4llm.to_markdown(str(pdf_path))
            except Exception as e:
                logger.warning("[seed] PDF 파싱 실패 %s: %s", pdf_path.name, e)
                text = f"Document: {pdf_path.name}"

            chunk_count = _ingest_doc_to_chroma(doc_id, title, text, source_file=pdf_path.name)
            _upsert_internal_doc_db(db, doc_id, title, text, pdf_path.name, chunk_count)
            logger.info("[seed] ingested '%s' → doc_id=%s, chunks=%d",
                        pdf_path.name, doc_id, chunk_count)
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_collections()
    _seed_internal_docs_from_dir()


# ── 헬스체크 ──────────────────────────────────────────────────
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "internal-service"}


# ── 사내문서 목록 ──────────────────────────────────────────────
@app.get("/internal-docs/")
def list_internal_docs(db: Session = Depends(get_db)) -> list:
    docs = db.query(InternalDocument).order_by(InternalDocument.created_at.desc()).all()
    return [
        {
            "doc_id": d.doc_id,
            "title": d.title,
            "source_file": d.source_file,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


# ── 사내문서 등록 (텍스트) ────────────────────────────────────
class RegisterDocRequest(BaseModel):
    title: str
    text: str
    doc_id: str | None = None


@app.post("/internal-docs/register")
def register_internal_doc(payload: RegisterDocRequest, db: Session = Depends(get_db)) -> dict:
    doc_id = payload.doc_id or f"internal-{uuid.uuid4().hex[:16]}"
    chunk_count = _ingest_doc_to_chroma(doc_id, payload.title, payload.text)
    _upsert_internal_doc_db(db, doc_id, payload.title, payload.text, "", chunk_count)
    return {"doc_id": doc_id, "title": payload.title, "chunk_count": chunk_count}


# ── 사내문서 등록 (PDF 업로드) ────────────────────────────────
@app.post("/internal-docs/upload")
async def upload_internal_doc(
    title: str = Form(...),
    doc_id: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    content = await file.read()
    text = _extract_pdf_text(content, file.filename)
    if not text.strip():
        raise HTTPException(status_code=422, detail="PDF에서 텍스트를 추출할 수 없습니다.")

    real_doc_id = doc_id or f"internal-{uuid.uuid4().hex[:16]}"
    chunk_count = _ingest_doc_to_chroma(real_doc_id, title, text, source_file=file.filename)
    _upsert_internal_doc_db(db, real_doc_id, title, text, file.filename, chunk_count)
    return {"doc_id": real_doc_id, "title": title, "chunk_count": chunk_count,
            "source_file": file.filename}


# ── 사내문서 삭제 ─────────────────────────────────────────────
@app.delete("/internal-docs/{doc_id}")
def delete_internal_doc(doc_id: str, db: Session = Depends(get_db)) -> dict:
    col = get_chroma_client().get_or_create_collection(
        os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs")
    )
    try:
        col.delete(where={"doc_id": doc_id})
    except Exception:
        pass
    db.query(InternalDocument).filter(InternalDocument.doc_id == doc_id).delete()
    db.commit()
    return {"deleted": doc_id}


# ── 사내문서 텍스트 조회 (ChromaDB) ──────────────────────────
@app.get("/internal-docs/{doc_id}")
def get_internal_doc_text(doc_id: str) -> dict:
    try:
        doc = _get_internal_doc_from_chroma(doc_id)
        full_text = "\n\n".join(chunk.document for chunk in doc.internal_chunks)
        return {"doc_id": doc_id, "title": doc.internal_doc_title, "text": full_text}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── PDF 파일 서빙 ─────────────────────────────────────────────
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
def get_internal_doc_by_id(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(InternalDocument).filter_by(doc_id=doc_id).first()
    if doc and doc.source_file:
        file_path = INTERNAL_DOCS_DIR / Path(doc.source_file).name
        if file_path.exists():
            return FileResponse(str(file_path), media_type="application/pdf",
                                headers={"Content-Disposition": f'inline; filename="{file_path.name}"'})
    raise HTTPException(status_code=404, detail=f"PDF not found for doc_id: {doc_id}")


# ── 레거시 ingest 엔드포인트 ──────────────────────────────────
class IngestRequest(BaseModel):
    doc_id: str
    title: str
    text: str


@app.post("/ingest/internal")
def ingest_internal(payload: IngestRequest) -> dict:
    chunks = chunk_text(payload.text)
    embeddings = embed_chunks(chunks)
    metadata = build_metadata(payload.doc_id, "internal", payload.title)

    client = get_chroma_client()
    collection = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs"))

    ids = [f"{payload.doc_id}-{idx}" for idx in range(len(chunks))]
    collection.add(ids=ids, documents=chunks, embeddings=embeddings,
                   metadatas=[metadata for _ in chunks])
    return {"ingested": len(chunks), "collection": "internal_docs"}


@app.post("/ingest/paper")
def ingest_paper(payload: IngestRequest) -> dict:
    chunks = chunk_text(payload.text)
    embeddings = embed_chunks(chunks)
    metadata = build_metadata(payload.doc_id, "paper", payload.title)

    client = get_chroma_client()
    collection = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_PAPERS", "papers"))

    ids = [f"{payload.doc_id}-{idx}" for idx in range(len(chunks))]
    collection.add(ids=ids, documents=chunks, embeddings=embeddings,
                   metadatas=[metadata for _ in chunks])
    return {"ingested": len(chunks), "collection": "papers"}

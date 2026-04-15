from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from ..database import SessionLocal
from ..models import ReportRecord
from ..schemas.report import FinalResponse
from ..chroma_client import get_chroma_client
from ..ingestion import chunk_text, embed_chunks

COLLECTION_REPORTS = os.getenv("CHROMA_COLLECTION_REPORTS", "reports")


def _utc_naive(dt) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _to_record(response: FinalResponse) -> ReportRecord:
    return ReportRecord(
        report_id=response.report_id,
        paper_id=response.paper_id,
        internal_doc_id=response.internal_doc_id,
        status=response.status,
        created_at=_utc_naive(response.created_at),
        updated_at=_utc_naive(response.updated_at),
        report_json=response.model_dump_json(),
    )


def _store_in_chroma(response: FinalResponse) -> None:
    client = get_chroma_client()
    col = client.get_or_create_collection(COLLECTION_REPORTS)

    sections = response.report.sections.model_dump()
    all_chunks, all_ids, all_metas = [], [], []
    for section_code, text in sections.items():
        if not text:
            continue
        chunks = chunk_text(str(text))
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{response.report_id}-{section_code}-{i}")
            all_metas.append({
                "report_id": response.report_id,
                "paper_id": response.paper_id,
                "internal_doc_id": response.internal_doc_id,
                "section_code": section_code,
                "created_at": str(response.created_at or ""),
            })

    if all_chunks:
        embeddings = embed_chunks(all_chunks)
        col.upsert(ids=all_ids, documents=all_chunks, embeddings=embeddings, metadatas=all_metas)


def save_report(response: FinalResponse) -> None:
    db = SessionLocal()
    try:
        rec = _to_record(response)
        db.merge(rec)
        db.commit()
    finally:
        db.close()
    _store_in_chroma(response)


def get_report(report_id: str) -> FinalResponse | None:
    db = SessionLocal()
    try:
        rec = db.query(ReportRecord).filter_by(report_id=report_id).first()
        if not rec or not rec.report_json:
            return None
        return FinalResponse.model_validate_json(rec.report_json)
    finally:
        db.close()


def get_latest_report() -> FinalResponse | None:
    db = SessionLocal()
    try:
        rec = (
            db.query(ReportRecord)
            .order_by(ReportRecord.updated_at.is_(None), ReportRecord.updated_at.desc())
            .first()
        )
        if not rec or not rec.report_json:
            return None
        return FinalResponse.model_validate_json(rec.report_json)
    finally:
        db.close()


def _extract_category(report_json: str | None) -> str | None:
    if not report_json:
        return None
    try:
        data = json.loads(report_json)
        for cit in data.get("citations", []):
            if cit.get("source_type") == "paper":
                return cit.get("metadata", {}).get("category")
    except Exception:
        pass
    return None


def list_reports(limit: int = 50) -> list[dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(ReportRecord)
            .order_by(ReportRecord.updated_at.is_(None), ReportRecord.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "report_id": r.report_id,
                "title": (json.loads(r.report_json).get("report", {}).get("title") if r.report_json else None) or r.report_id,
                "paper_id": r.paper_id,
                "internal_doc_id": r.internal_doc_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "category": _extract_category(r.report_json),
            }
            for r in rows
        ]
    finally:
        db.close()

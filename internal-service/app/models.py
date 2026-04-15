from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from .database import Base


class ReportRecord(Base):
    __tablename__ = "report"
    report_id = Column(String(255), primary_key=True)
    paper_id = Column(String(255), nullable=True)
    internal_doc_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    report_json = Column(Text, nullable=True)


class InternalDocument(Base):
    __tablename__ = "internal_document"

    doc_id        = Column(String(255), primary_key=True)
    title         = Column(String(1024), nullable=False)
    original_text = Column(Text, nullable=True)
    source_file   = Column(String(1024), nullable=True)
    chunk_count   = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)

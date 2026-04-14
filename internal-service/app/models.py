from sqlalchemy import Column, String, Text, DateTime
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

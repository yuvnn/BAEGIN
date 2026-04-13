from sqlalchemy import Column, String, Text, Integer, ForeignKey
from .database import Base

class PaperSummary(Base):
    __tablename__ = "paper_summary"

    paper_id = Column(String(255), primary_key=True, index=True)
    md_summary = Column(Text)
    paper_url = Column(String(1024))
    authors = Column(Text)  # Stored as JSON string
    category = Column(String(255))

class PaperRelate(Base):
    __tablename__ = "paper_relate"

    paper_id = Column(String(255), ForeignKey("paper_summary.paper_id"), primary_key=True)
    internal_doc_id = Column(String(255), primary_key=True)
    rank = Column(Integer)
    reason = Column(Text)  # Markdown text explaining the relation

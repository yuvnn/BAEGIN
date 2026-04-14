from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey
from .database import Base


class Paper(Base):
    __tablename__ = "paper"

    paper_id         = Column(String(255), primary_key=True, index=True)
    title            = Column(String(1024), nullable=True)
    abstract         = Column(Text, nullable=True)
    authors          = Column(Text, nullable=True)       # JSON string
    published_at     = Column(DateTime, nullable=True, index=True)
    detected_at      = Column(DateTime, nullable=True)
    source           = Column(String(50), nullable=True)  # arxiv / huggingface
    url              = Column(String(1024), nullable=True)
    pdf_url          = Column(String(1024), nullable=True)
    arxiv_categories = Column(String(512), nullable=True)  # comma-joined
    category         = Column(String(255), nullable=True)


class PaperSummary(Base):
    __tablename__ = "paper_summary"

    paper_id      = Column(String(255), ForeignKey("paper.paper_id"), primary_key=True, index=True)
    md_summary    = Column(Text)
    paper_url     = Column(String(1024))
    authors       = Column(Text)          # Stored as JSON string (kept for compatibility)
    category      = Column(String(255))
    aira_score    = Column(Float, nullable=True)
    aira_decision = Column(String(50), nullable=True)


class PaperRelate(Base):
    __tablename__ = "paper_relate"

    paper_id        = Column(String(255), ForeignKey("paper_summary.paper_id"), primary_key=True)
    internal_doc_id = Column(String(255), primary_key=True)
    rank            = Column(Integer)
    reason          = Column(Text)

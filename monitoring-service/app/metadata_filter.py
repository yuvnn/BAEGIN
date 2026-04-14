import logging
import os

logger = logging.getLogger(__name__)

TOP_CONFERENCES = [
    "NeurIPS", "ICLR", "ICML", "ACL", "EMNLP",
    "CVPR", "ICCV", "ECCV", "AAAI", "NAACL",
    "SIGKDD", "IJCAI",
]
HF_UPVOTE_THRESHOLD = int(os.getenv("HF_UPVOTE_THRESHOLD", "2"))

# arXiv AI/ML 관련 카테고리 — 이 카테고리에 속한 논문은 바로 통과
AI_ML_CATEGORIES = {
    "cs.CL", "cs.CV", "cs.LG", "cs.AI", "cs.NE", "cs.RO",
    "cs.MA", "cs.IR", "cs.HC", "cs.GT", "cs.SY",
    "stat.ML", "eess.SP", "eess.IV",
}


def _has_conference_mention(paper: dict) -> bool:
    comment = paper.get("comment", "") or ""
    title = paper.get("title", "") or ""
    abstract = paper.get("abstract", "") or ""
    text = (comment + " " + title + " " + abstract[:500]).upper()
    return any(conf.upper() in text for conf in TOP_CONFERENCES)


def _is_huggingface(paper: dict) -> bool:
    """HuggingFace Daily Papers는 이미 AI/ML 큐레이션 플랫폼이므로 전부 통과."""
    return paper.get("source") == "huggingface"


def _has_hf_upvotes(paper: dict) -> bool:
    return paper.get("source") == "huggingface" and paper.get("upvotes", 0) >= HF_UPVOTE_THRESHOLD


def _is_ai_ml_arxiv(paper: dict) -> bool:
    """arXiv 논문이 AI/ML 카테고리에 속하면 통과 (신규 논문은 컨퍼런스 게재 전이라 conference 언급이 없음)."""
    cats = paper.get("arxiv_categories") or []
    return bool(set(cats) & AI_ML_CATEGORIES)


def filter_by_metadata(papers: list[dict]) -> list[dict]:
    """Stage 1: Fast code-only filter.
    Pass if: (1) conference mention, (2) HuggingFace paper (already AI/ML curated),
    or (3) arXiv paper in AI/ML category.
    """
    result = [
        p for p in papers
        if _has_conference_mention(p) or _is_huggingface(p) or _is_ai_ml_arxiv(p)
    ]
    logger.info(
        "metadata_filter: %d → %d (conference mention OR HuggingFace OR AI/ML arXiv category)",
        len(papers), len(result),
    )
    return result

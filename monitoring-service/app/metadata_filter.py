import logging

logger = logging.getLogger(__name__)

TOP_CONFERENCES = [
    "NeurIPS", "ICLR", "ICML", "ACL", "EMNLP",
    "CVPR", "ICCV", "ECCV", "AAAI", "NAACL",
    "SIGKDD", "IJCAI",
]
HF_UPVOTE_THRESHOLD = 5


def _has_conference_mention(paper: dict) -> bool:
    comment = paper.get("comment", "") or ""
    title = paper.get("title", "") or ""
    text = (comment + " " + title).upper()
    return any(conf.upper() in text for conf in TOP_CONFERENCES)


def _has_hf_upvotes(paper: dict) -> bool:
    return paper.get("source") == "huggingface" and paper.get("upvotes", 0) >= HF_UPVOTE_THRESHOLD


def filter_by_metadata(papers: list[dict]) -> list[dict]:
    """Stage 1: Fast code-only filter using conference mentions and HF upvotes."""
    result = [
        p for p in papers
        if _has_conference_mention(p) or _has_hf_upvotes(p)
    ]
    logger.info(
        "metadata_filter: %d → %d (conference mention or HF upvotes >= %d)",
        len(papers), len(result), HF_UPVOTE_THRESHOLD,
    )
    return result

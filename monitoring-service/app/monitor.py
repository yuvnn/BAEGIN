from datetime import datetime


def fetch_mock_papers(keyword: str) -> list[dict]:
    # TODO: replace with arXiv/Crossref/PubMed connector.
    return [
        {
            "paper_id": f"paper-{keyword}-001",
            "title": f"Latest Research about {keyword}",
            "abstract": f"This paper discusses novel methods around {keyword}.",
            "published_at": datetime.utcnow().isoformat(),
        }
    ]

import os

import chromadb


def get_client() -> chromadb.HttpClient:
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    return chromadb.HttpClient(host=host, port=port)


def compare_with_internal_docs(query_text: str, top_k: int = 3) -> dict:
    client = get_client()
    paper_col = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_PAPERS", "papers"))
    internal_col = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs"))

    paper_hits = paper_col.query(query_texts=[query_text], n_results=top_k)
    internal_hits = internal_col.query(query_texts=[query_text], n_results=top_k)

    return {
        "paper_hits": paper_hits,
        "internal_hits": internal_hits,
    }

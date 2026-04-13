import os

import chromadb


def get_chroma_client() -> chromadb.HttpClient:
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    return chromadb.HttpClient(host=host, port=port)


def ensure_collections() -> None:
    client = get_chroma_client()
    client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_PAPERS", "papers"))
    client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs"))

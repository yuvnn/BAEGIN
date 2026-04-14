import os
from pathlib import Path

import chromadb


def get_chroma_client() -> chromadb.ClientAPI:
    mode = os.getenv("CHROMA_MODE", "http").lower()
    if mode == "persistent":
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parents[2] / "data" / "chroma"))
        return chromadb.PersistentClient(path=persist_dir)

    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    try:
        client = chromadb.HttpClient(host=host, port=port)
        # Force a lightweight connectivity check during startup.
        client.heartbeat()
        return client
    except Exception:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parents[2] / "data" / "chroma"))
        return chromadb.PersistentClient(path=persist_dir)


def ensure_collections() -> None:
    client = get_chroma_client()
    client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_PAPERS", "papers"))
    client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs"))

import os
import chromadb
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_PAPERS", "papers")

_client = None
_collection = None

def get_chroma_client():
    global _client
    if _client is None:
        logger.info(f"Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}")
        _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return _client

def ensure_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection

def store_paper(doc_id: str, summary: str, metadata: Dict[str, Any]):
    """
    Stores the paper summary and metadata into ChromaDB.
    """
    try:
        collection = ensure_collection()
        collection.upsert(
            ids=[doc_id],
            documents=[summary],
            metadatas=[metadata]
        )
        logger.info(f"Stored paper {doc_id} into ChromaDB")
    except Exception as e:
        logger.error(f"Failed to store paper {doc_id} in ChromaDB: {e}")

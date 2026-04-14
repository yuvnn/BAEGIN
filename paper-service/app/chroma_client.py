import os
import chromadb
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_PAPERS", "papers")
INTERNAL_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_INTERNAL", "internal_docs")

_client = None
_collection = None
_internal_collection = None

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

def ensure_internal_collection():
    global _internal_collection
    if _internal_collection is None:
        client = get_chroma_client()
        _internal_collection = client.get_or_create_collection(name=INTERNAL_COLLECTION_NAME)
    return _internal_collection

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

def get_recent_papers(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches recently evaluated and summarized papers from ChromaDB.
    """
    try:
        collection = ensure_collection()
        results = collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        papers = []
        if results and "ids" in results and results["ids"]:
            for i in range(len(results["ids"])):
                papers.append({
                    "paper_id": results["ids"][i],
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
        return papers
    except Exception as e:
        logger.error(f"Failed to fetch papers from ChromaDB: {e}")
        return []

def query_internal_docs(query_text: str, n_results: int = 50) -> Dict[str, Any]:
    """
    Queries the internal_docs collection to find similar chunks for the paper summary.
    """
    try:
        collection = ensure_internal_collection()
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
    except Exception as e:
        logger.error(f"Failed to query internal_docs in ChromaDB: {e}")
        return {}

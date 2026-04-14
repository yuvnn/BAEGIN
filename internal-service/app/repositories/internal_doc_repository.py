from __future__ import annotations

from ..chroma_client import get_chroma_client
from ..schemas.input import InternalDoc

def get_internal_doc(internal_doc_id: str) -> InternalDoc:
    client = get_chroma_client()
    collection = client.get_or_create_collection("internal_docs")
    result = collection.get(where={"doc_id": internal_doc_id}, include=["documents", "metadatas"])

    ids = result.get("ids") or []
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    if not ids or not documents:
        raise ValueError(f"internal_docs collection에 doc_id={internal_doc_id} 문서가 없습니다")

    chunks = []
    for idx, (chunk_id, doc_text) in enumerate(zip(ids, documents)):
        md = metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {}
        chunk_id_str = str(chunk_id)
        if isinstance(md.get("chunk_index"), int):
            chunk_index = md.get("chunk_index")
        else:
            try:
                chunk_index = int(chunk_id_str.rsplit("-", 1)[-1])
            except Exception:
                chunk_index = idx

        chunks.append(
            {
                "chunk_id": chunk_id_str,
                "document": str(doc_text),
                "metadata": {
                    "doc_id": str(md.get("doc_id", internal_doc_id)),
                    "source_type": str(md.get("source_type", "internal")),
                    "title": str(md.get("title", f"Chroma internal doc {internal_doc_id}")),
                    "source_file": str(md.get("source_file", "unknown.pdf")),
                    "source_ext": str(md.get("source_ext", ".pdf")),
                    "chunk_index": chunk_index,
                    "doc_version": str(md.get("doc_version", "v1")),
                    "page_no": md.get("page_no"),
                    "chunk_char_start": md.get("chunk_char_start"),
                    "chunk_char_end": md.get("chunk_char_end"),
                },
            }
        )

    chunks.sort(key=lambda c: c["metadata"]["chunk_index"])
    return InternalDoc.model_validate(
        {
            "internal_doc_id": internal_doc_id,
            "internal_doc_title": str((metadatas[0] or {}).get("title", f"Chroma internal doc {internal_doc_id}")),
            "internal_chunks": chunks,
        }
    )

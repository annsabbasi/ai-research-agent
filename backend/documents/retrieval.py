"""Similarity search over the user's document chunks (the 'R' in RAG).

`format_result` / `_similarity` are pure so they can be unit-tested without a
database; the ORM + pgvector query lives in `retrieve_from_documents`, with all
heavy imports done lazily so the module loads cheaply.
"""

from typing import List, Optional


def _similarity(distance: float) -> float:
    """Convert cosine *distance* (0 = identical) to a 0..1 similarity score."""
    return round(1.0 - float(distance), 4)


def format_result(
    *,
    title: str,
    document_id: int,
    chunk_index: int,
    content: str,
    distance: float,
    snippet_len: int = 200,
) -> dict:
    """Shape a retrieved chunk into a source dict the agent can cite."""
    return {
        "type": "document",
        "title": title,
        "document_id": document_id,
        "chunk_index": chunk_index,
        "content": content,
        "snippet": content[:snippet_len],
        "url": "",  # internal documents have no external URL
        "score": _similarity(distance),
    }


def retrieve_from_documents(
    query: str,
    user_id: int,
    top_k: Optional[int] = None,
    embedder=None,
) -> List[dict]:
    """Return the top-k most relevant chunks from the user's completed docs.

    Scoped to `user_id` so one user can never retrieve another's documents.
    `embedder` is injectable for testing.
    """
    if not (query or "").strip():
        return []

    from django.conf import settings
    from pgvector.django import CosineDistance

    from .models import Document, DocumentChunk
    from .rag import embed_query

    top_k = top_k or getattr(settings, "RAG_TOP_K", 5)
    query_vector = embed_query(query, embedder=embedder)

    rows = (
        DocumentChunk.objects.filter(
            user_id=user_id, document__status=Document.Status.COMPLETED
        )
        .annotate(distance=CosineDistance("embedding", query_vector))
        .select_related("document")
        .order_by("distance")[:top_k]
    )

    return [
        format_result(
            title=row.document.title,
            document_id=row.document_id,
            chunk_index=row.chunk_index,
            content=row.content,
            distance=row.distance,
        )
        for row in rows
    ]

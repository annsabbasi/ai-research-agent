import logging

from celery import shared_task
from django.conf import settings

from .rag import chunk_text, embed_texts, fetch_url_text

logger = logging.getLogger(__name__)


def _extract_text(document) -> str:
    """Return the raw text for a document based on its source type."""
    from .models import Document

    if document.source_type == Document.SourceType.URL:
        return fetch_url_text(document.source_ref)
    # TEXT: the pasted text is stored directly in source_ref.
    return document.source_ref or ""


@shared_task(bind=True, max_retries=2, acks_late=True)
def ingest_document_task(self, document_id):
    """Extract -> chunk -> embed -> store chunks for a single document.

    Idempotent: re-running replaces the document's existing chunks, so a retry
    or re-ingest never leaves duplicates behind.
    """
    from .models import Document, DocumentChunk

    try:
        document = Document.objects.get(id=document_id)
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status"])

        text = _extract_text(document)
        chunks = chunk_text(
            text,
            chunk_size=getattr(settings, "RAG_CHUNK_SIZE", 800),
            overlap=getattr(settings, "RAG_CHUNK_OVERLAP", 120),
        )
        if not chunks:
            raise ValueError("No text could be extracted from the document.")

        vectors = embed_texts(chunks)

        chunk_objs = [
            DocumentChunk(
                document=document,
                user_id=document.user_id,
                chunk_index=i,
                content=content,
                embedding=vector,
            )
            for i, (content, vector) in enumerate(zip(chunks, vectors))
        ]

        # Replace any prior chunks so re-ingestion stays idempotent.
        document.chunks.all().delete()
        DocumentChunk.objects.bulk_create(chunk_objs)

        document.chunk_count = len(chunk_objs)
        document.status = Document.Status.COMPLETED
        document.error = ""
        document.save(update_fields=["chunk_count", "status", "error"])

        return {"document_id": document_id, "chunks": len(chunk_objs)}

    except Exception as exc:
        logger.exception("Document ingestion failed for document %s", document_id)
        try:
            document = Document.objects.get(id=document_id)
            document.status = Document.Status.FAILED
            document.error = str(exc)[:1000]
            document.save(update_fields=["status", "error"])
        except Document.DoesNotExist:
            pass
        raise self.retry(exc=exc, countdown=20)

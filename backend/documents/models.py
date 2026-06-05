from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField

EMBEDDING_DIMENSIONS = getattr(settings, "EMBEDDING_DIMENSIONS", 1536)


class Document(models.Model):
    """A user-uploaded source the agent can retrieve from (the RAG corpus)."""

    class SourceType(models.TextChoices):
        TEXT = "text", "Pasted text"
        PDF = "pdf", "PDF upload"
        URL = "url", "Web URL"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    source_type = models.CharField(
        max_length=10, choices=SourceType.choices, default=SourceType.TEXT
    )
    # Original source location (URL) or filename; raw pasted text lives here too.
    source_ref = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error = models.TextField(blank=True, default="")
    chunk_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title[:80]


class DocumentChunk(models.Model):
    """A single embedded slice of a Document, used for similarity search."""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )
    # Denormalised for query-time filtering without a join to Document.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_chunks",
    )
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["document_id", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="uniq_chunk_per_document",
            )
        ]
        indexes = [
            # Approximate-nearest-neighbour index for cosine distance so
            # similarity search stays fast as the corpus grows.
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["user"], name="chunk_user_idx"),
        ]

    def __str__(self):
        return f"{self.document_id}#{self.chunk_index}"

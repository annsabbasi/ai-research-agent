import hashlib

from django.conf import settings
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags"
    )

    class Meta:
        unique_together = ("name", "user")
        db_table = "tags"

    def __str__(self):
        return self.name


class ResearchQuery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_queries",
    )
    question = models.TextField()
    query_hash = models.CharField(max_length=64, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="queries")
    celery_task_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "research_queries"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]

    def save(self, *args, **kwargs):
        if not self.query_hash:
            self.query_hash = hashlib.sha256(
                self.question.strip().lower().encode()
            ).hexdigest()
        super().save(*args, **kwargs)


class ResearchResult(models.Model):
    query = models.OneToOneField(
        ResearchQuery, on_delete=models.CASCADE, related_name="result"
    )
    summary = models.TextField(blank=True, default="")
    sources = models.JSONField(default=list)
    sub_queries = models.JSONField(default=list)
    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_results"

    def __str__(self):
        return f"Result for: {self.query.question[:50]}"

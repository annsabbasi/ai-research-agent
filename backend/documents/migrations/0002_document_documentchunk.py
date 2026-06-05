import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from pgvector.django import HnswIndex, VectorField


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ("documents", "0001_enable_pgvector"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                (
                    "source_type",
                    models.CharField(
                        choices=[("text", "Pasted text"), ("pdf", "PDF upload"), ("url", "Web URL")],
                        default="text",
                        max_length=10,
                    ),
                ),
                ("source_ref", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error", models.TextField(blank=True, default="")),
                ("chunk_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "documents",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_index", models.PositiveIntegerField()),
                ("content", models.TextField()),
                ("embedding", VectorField(dimensions=1536)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="documents.document",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_chunks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "document_chunks",
                "ordering": ["document_id", "chunk_index"],
            },
        ),
        migrations.AddConstraint(
            model_name="documentchunk",
            constraint=models.UniqueConstraint(
                fields=["document", "chunk_index"], name="uniq_chunk_per_document"
            ),
        ),
        migrations.AddIndex(
            model_name="documentchunk",
            index=HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="documentchunk",
            index=models.Index(fields=["user"], name="chunk_user_idx"),
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="tags",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "db_table": "tags",
                "unique_together": {("name", "user")},
            },
        ),
        migrations.CreateModel(
            name="ResearchQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField()),
                ("query_hash", models.CharField(db_index=True, max_length=64)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("processing", "Processing"),
                        ("completed", "Completed"),
                        ("failed", "Failed"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("celery_task_id", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="research_queries",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("tags", models.ManyToManyField(blank=True, related_name="queries", to="research.tag")),
            ],
            options={
                "db_table": "research_queries",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ResearchResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("summary", models.TextField(blank=True, default="")),
                ("sources", models.JSONField(default=list)),
                ("sub_queries", models.JSONField(default=list)),
                ("raw_data", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("query", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="result",
                    to="research.researchquery",
                )),
            ],
            options={
                "db_table": "research_results",
            },
        ),
    ]

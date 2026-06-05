from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    """Enable the Postgres `vector` extension before any VectorField is created.

    Runs first in the documents app so the embedding column in the next
    migration has the `vector` type available.
    """

    initial = True

    dependencies = []

    operations = [
        VectorExtension(),
    ]

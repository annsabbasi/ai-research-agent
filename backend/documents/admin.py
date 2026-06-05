from django.contrib import admin

from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "source_type", "status", "chunk_count", "created_at")
    list_filter = ("status", "source_type")
    search_fields = ("title", "source_ref")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "chunk_index", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("content",)

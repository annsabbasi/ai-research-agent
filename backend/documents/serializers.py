from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Read serializer for listing/detail of a document."""

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "source_type",
            "source_ref",
            "status",
            "error",
            "chunk_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DocumentCreateSerializer(serializers.Serializer):
    """Input serializer for creating a document from pasted text or a URL."""

    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    source_type = serializers.ChoiceField(
        choices=[("text", "text"), ("url", "url")], default="text"
    )
    content = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, data):
        source_type = data.get("source_type", "text")
        if source_type == "text" and not (data.get("content") or "").strip():
            raise serializers.ValidationError(
                {"content": "Required when source_type is 'text'."}
            )
        if source_type == "url" and not (data.get("url") or "").strip():
            raise serializers.ValidationError(
                {"url": "Required when source_type is 'url'."}
            )
        return data

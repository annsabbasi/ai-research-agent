from rest_framework import serializers

from .models import ResearchQuery, ResearchResult, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")
        read_only_fields = ("id",)


class ResearchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchResult
        fields = ("id", "summary", "sources", "sub_queries", "created_at")


class ResearchQueryListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchQuery
        fields = (
            "id",
            "question",
            "status",
            "tags",
            "created_at",
            "updated_at",
        )


class ResearchQueryDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    result = ResearchResultSerializer(read_only=True)

    class Meta:
        model = ResearchQuery
        fields = (
            "id",
            "question",
            "query_hash",
            "status",
            "tags",
            "result",
            "created_at",
            "updated_at",
        )


class ResearchQueryCreateSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=10, max_length=1000)


class TagCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=50)

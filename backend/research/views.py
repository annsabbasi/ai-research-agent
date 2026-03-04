import hashlib

from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ResearchQuery, ResearchResult, Tag
from .serializers import (
    ResearchQueryCreateSerializer,
    ResearchQueryDetailSerializer,
    ResearchQueryListSerializer,
    TagCreateSerializer,
    TagSerializer,
)
from .tasks import run_research_task


class ResearchQueryCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ResearchQueryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        query_hash = hashlib.sha256(question.strip().lower().encode()).hexdigest()
        cache_key = f"research:{query_hash}"
        cached_data = cache.get(cache_key)

        query = ResearchQuery.objects.create(
            user=request.user, question=question, query_hash=query_hash
        )

        if cached_data:
            query.status = ResearchQuery.Status.COMPLETED
            query.save()
            ResearchResult.objects.create(
                query=query,
                summary=cached_data.get("summary", ""),
                sources=cached_data.get("sources", []),
                sub_queries=cached_data.get("sub_queries", []),
                raw_data=cached_data.get("raw_data", {}),
            )
            return Response(
                ResearchQueryDetailSerializer(query).data,
                status=status.HTTP_201_CREATED,
            )

        task = run_research_task.delay(query.id)
        query.celery_task_id = task.id
        query.save(update_fields=["celery_task_id"])

        return Response(
            ResearchQueryDetailSerializer(query).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ResearchQueryListView(generics.ListAPIView):
    serializer_class = ResearchQueryListSerializer

    def get_queryset(self):
        return ResearchQuery.objects.filter(user=self.request.user)


class ResearchQueryDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ResearchQueryDetailSerializer

    def get_queryset(self):
        return ResearchQuery.objects.filter(user=self.request.user)


class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)


class ResearchQueryTagView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        query = ResearchQuery.objects.get(pk=pk, user=request.user)
        serializer = TagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag, _ = Tag.objects.get_or_create(
            name=serializer.validated_data["name"], user=request.user
        )
        query.tags.add(tag)

        return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)

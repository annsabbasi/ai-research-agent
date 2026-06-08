from rest_framework import generics, status
from rest_framework.response import Response

from .models import Document
from .serializers import DocumentCreateSerializer, DocumentSerializer
from .tasks import ingest_document_task


class DocumentListCreateView(generics.ListCreateAPIView):
    """GET: list the user's documents. POST: create one and start ingestion."""

    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = DocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        source_type = data["source_type"]
        if source_type == Document.SourceType.URL:
            source_ref = data["url"]
            default_title = data["url"]
        else:
            source_ref = data["content"]
            default_title = data["content"][:60]

        document = Document.objects.create(
            user=request.user,
            title=(data.get("title") or default_title).strip() or "Untitled",
            source_type=source_type,
            source_ref=source_ref,
        )

        ingest_document_task.delay(document.id)

        return Response(
            DocumentSerializer(document).data, status=status.HTTP_202_ACCEPTED
        )


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """GET / DELETE a single document owned by the user."""

    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

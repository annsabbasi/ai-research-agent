from django.urls import path

from .views import (
    ResearchQueryCreateView,
    ResearchQueryDetailView,
    ResearchQueryListView,
    ResearchQueryTagView,
    TagListView,
)

urlpatterns = [
    path("", ResearchQueryCreateView.as_view(), name="research-create"),
    path("list/", ResearchQueryListView.as_view(), name="research-list"),
    path("<int:pk>/", ResearchQueryDetailView.as_view(), name="research-detail"),
    path("<int:pk>/tags/", ResearchQueryTagView.as_view(), name="research-tags"),
    path("tags/", TagListView.as_view(), name="tag-list"),
]

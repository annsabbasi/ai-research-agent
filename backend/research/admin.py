from django.contrib import admin

from .models import ResearchQuery, ResearchResult, Tag

admin.site.register(Tag)
admin.site.register(ResearchQuery)
admin.site.register(ResearchResult)

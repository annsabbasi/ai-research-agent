import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache

logger = logging.getLogger(__name__)


def send_ws_update(query_id, message_type, status, detail="", data=None):
    channel_layer = get_channel_layer()
    group_name = f"research_{query_id}"
    message = {
        "type": "research.update",
        "message": {
            "type": message_type,
            "status": status,
            "detail": detail,
        },
    }
    if data:
        message["message"]["data"] = data
    async_to_sync(channel_layer.group_send)(group_name, message)


@shared_task(bind=True, max_retries=2, acks_late=True)
def run_research_task(self, query_id):
    from .models import ResearchQuery, ResearchResult

    try:
        query = ResearchQuery.objects.get(id=query_id)
        query.status = ResearchQuery.Status.PROCESSING
        query.save(update_fields=["status"])

        send_ws_update(query_id, "status", "processing", "Starting research...")

        stage_messages = {
            "planning": "Breaking down your question into sub-queries...",
            "searching": "Searching the web for information...",
            "reflecting": "Reflecting on the evidence gathered so far...",
            "analyzing": "Analyzing search results...",
            "formatting": "Formatting the final report...",
        }

        def status_callback(stage, detail="", meta=None):
            send_ws_update(
                query_id,
                "status",
                stage,
                detail or stage_messages.get(stage, f"Working: {stage}..."),
            )

        from agent.graph import run_research

        result_state = run_research(query.question, status_callback=status_callback)

        result = ResearchResult.objects.create(
            query=query,
            summary=result_state.get("report", ""),
            sources=result_state.get("sources", []),
            sub_queries=result_state.get("sub_queries", []),
            raw_data={
                "analysis": result_state.get("analysis", ""),
                "iterations": result_state.get("iteration", 0),
                "knowledge_gaps": result_state.get("knowledge_gaps", []),
                "executed_queries": result_state.get("executed_queries", []),
            },
        )

        query.status = ResearchQuery.Status.COMPLETED
        query.save(update_fields=["status"])

        # Cache the result
        cache_key = f"research:{query.query_hash}"
        cache_data = {
            "summary": result.summary,
            "sources": result.sources,
            "sub_queries": result.sub_queries,
            "raw_data": result.raw_data,
        }
        cache.set(cache_key, cache_data, timeout=86400)  # 24h TTL

        send_ws_update(
            query_id,
            "result",
            "completed",
            "Research complete!",
            data={
                "summary": result.summary,
                "sources": result.sources,
                "sub_queries": result.sub_queries,
            },
        )

        return {"status": "completed", "query_id": query_id}

    except Exception as exc:
        logger.exception(f"Research task failed for query {query_id}")
        try:
            query = ResearchQuery.objects.get(id=query_id)
            query.status = ResearchQuery.Status.FAILED
            query.save(update_fields=["status"])
        except ResearchQuery.DoesNotExist:
            pass

        send_ws_update(query_id, "status", "failed", str(exc))
        raise self.retry(exc=exc, countdown=30)

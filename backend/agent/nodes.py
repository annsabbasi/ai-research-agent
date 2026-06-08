import json

from langchain_openai import ChatOpenAI

from .prompts import (
    ANALYZE_PROMPT,
    FORMAT_PROMPT,
    PLAN_PROMPT,
    PLAN_PROMPT_WITH_DOCS,
    REFLECT_PROMPT,
)
from .streaming import emit_token
from .tools import search_documents, search_web

VALID_SOURCES = ("web", "documents", "both")


def get_llm():
    return ChatOpenAI(model="gpt-4o", temperature=0.1)


def _parse_json(content: str):
    """Best-effort extraction of a JSON value from an LLM response."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.lstrip().startswith("json"):
            content = content.lstrip()[4:]
    return json.loads(content.strip())


def _normalize_web_results(results: list) -> list:
    """Shape raw Tavily results into unified source dicts."""
    normalized = []
    for r in results:
        content = r.get("content", "") or ""
        normalized.append(
            {
                "type": "web",
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": content[:200],
                "content": content,
            }
        )
    return normalized


def plan_node(state: dict) -> dict:
    llm = get_llm()
    question = state["question"]
    has_docs = state.get("has_documents", False)

    if has_docs:
        response = llm.invoke(PLAN_PROMPT_WITH_DOCS.format(question=question))
        raw = _parse_json(response.content)
        pending = []
        for item in raw:
            if isinstance(item, dict):
                query = (item.get("query") or "").strip()
                source = item.get("source", "both")
            else:
                query, source = str(item).strip(), "both"
            if not query:
                continue
            if source not in VALID_SOURCES:
                source = "both"
            pending.append({"query": query, "source": source})
    else:
        response = llm.invoke(PLAN_PROMPT.format(question=question))
        raw = _parse_json(response.content)
        pending = [
            {"query": str(q).strip(), "source": "web"}
            for q in raw
            if str(q).strip()
        ]

    sub_queries = [p["query"] for p in pending]
    detail = f"Planning: broke the question into {len(pending)} sub-queries"
    if has_docs:
        detail += " (routing across your documents and the web)"

    return {
        **state,
        "pending_queries": pending,
        "sub_queries": sub_queries,
        "executed_queries": [],
        "stage": "planning",
        "stage_detail": detail,
    }


def search_node(state: dict) -> dict:
    """Execute pending sub-queries, routing each to web and/or documents."""
    pending = state.get("pending_queries") or []
    all_results = list(state.get("search_results", []))
    all_sources = list(state.get("sources", []))
    executed = list(state.get("executed_queries", []))
    seen = {
        (s.get("title", ""), s.get("url", ""), s.get("snippet", ""))
        for s in all_sources
    }

    for item in pending:
        if isinstance(item, dict):
            query, source = item.get("query", ""), item.get("source", "web")
        else:
            query, source = str(item), "web"
        if not query or query in executed:
            continue

        results = []
        if source in ("web", "both"):
            try:
                response = search_web(query)
                results += _normalize_web_results(response.get("results", []))
            except Exception:
                pass
        if source in ("documents", "both"):
            results += search_documents(query)

        all_results.append({"query": query, "source": source, "results": results})
        for r in results:
            # Keep stored sources lean: drop the full chunk/page content.
            entry = {k: v for k, v in r.items() if k != "content"}
            key = (entry.get("title", ""), entry.get("url", ""), entry.get("snippet", ""))
            if key not in seen:
                seen.add(key)
                all_sources.append(entry)
        executed.append(query)

    doc_total = sum(1 for s in all_sources if s.get("type") == "document")
    web_total = len(all_sources) - doc_total

    return {
        **state,
        "search_results": all_results,
        "sources": all_sources,
        "executed_queries": executed,
        "pending_queries": [],
        "stage": "searching",
        "stage_detail": (
            f"Searched {len(executed)} queries — {len(all_sources)} sources "
            f"({doc_total} from your documents, {web_total} from the web)"
        ),
    }


def reflect_node(state: dict) -> dict:
    """Decide whether the gathered evidence is sufficient, or plan follow-ups."""
    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", 2)

    if iteration > max_iterations:
        return {
            **state,
            "iteration": iteration,
            "is_sufficient": True,
            "pending_queries": [],
            "stage": "reflecting",
            "stage_detail": "Reached the research-round budget; proceeding to synthesis",
        }

    llm = get_llm()
    question = state["question"]
    executed = state.get("executed_queries", [])
    sources = state.get("sources", [])

    executed_text = "\n".join(f"- {q}" for q in executed) or "(none yet)"
    evidence_text = (
        "\n".join(f"- {s.get('title', 'N/A')}: {s.get('snippet', '')}" for s in sources)
        or "(no evidence gathered)"
    )

    try:
        response = llm.invoke(
            REFLECT_PROMPT.format(
                question=question,
                executed_queries=executed_text,
                evidence=evidence_text,
            )
        )
        verdict = _parse_json(response.content)
    except Exception:
        verdict = {"sufficient": True, "gaps": [], "new_queries": []}

    sufficient = bool(verdict.get("sufficient", True))
    gaps = verdict.get("gaps", []) or []
    new_queries = [] if sufficient else (verdict.get("new_queries", []) or [])
    new_queries = [q for q in new_queries if q not in executed]

    # Follow-ups can draw on documents too when the user has them.
    default_source = "both" if state.get("has_documents") else "web"
    pending = [{"query": q, "source": default_source} for q in new_queries]
    sub_queries = list(state.get("sub_queries", [])) + new_queries

    if sufficient or not new_queries:
        detail = "Evidence looks sufficient — moving on to analysis"
    else:
        detail = (
            f"Found {len(gaps)} gap(s); running {len(new_queries)} "
            f"follow-up search(es) (round {iteration})"
        )

    return {
        **state,
        "iteration": iteration,
        "is_sufficient": sufficient,
        "knowledge_gaps": gaps,
        "new_queries": new_queries,
        "pending_queries": pending,
        "sub_queries": sub_queries,
        "stage": "reflecting",
        "stage_detail": detail,
    }


def analyze_node(state: dict) -> dict:
    llm = get_llm()
    question = state["question"]
    search_results = state["search_results"]

    results_text = ""
    for item in search_results:
        results_text += f"\n### Query: {item['query']} (source: {item.get('source', 'web')})\n"
        for r in item.get("results", []):
            label = "DOC" if r.get("type") == "document" else "WEB"
            results_text += (
                f"- [{label}] **{r.get('title', 'N/A')}**: "
                f"{(r.get('content') or r.get('snippet') or 'N/A')[:500]}\n"
            )

    response = llm.invoke(
        ANALYZE_PROMPT.format(question=question, search_results=results_text)
    )

    return {
        **state,
        "analysis": response.content,
        "stage": "analyzing",
        "stage_detail": "Synthesizing findings across all gathered sources...",
    }


def format_node(state: dict) -> dict:
    llm = get_llm()
    question = state["question"]
    analysis = state["analysis"]
    sources = state["sources"]

    source_lines = []
    for s in sources:
        if s.get("url"):
            source_lines.append(f"- [{s['title']}]({s['url']})")
        elif s.get("type") == "document":
            source_lines.append(f"- {s.get('title', 'Document')} (your uploaded document)")
    sources_text = "\n".join(source_lines)

    prompt = FORMAT_PROMPT.format(
        question=question, analysis=analysis, sources=sources_text
    )

    # Stream the report token-by-token; accumulate the full text to persist.
    parts: list[str] = []
    for chunk in llm.stream(prompt):
        token = chunk.content or ""
        if token:
            parts.append(token)
            emit_token(token)

    report = "".join(parts)

    return {
        **state,
        "report": report,
        "stage": "formatting",
        "stage_detail": "Writing the final structured report...",
    }

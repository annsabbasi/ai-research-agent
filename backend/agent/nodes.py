import json

from langchain_openai import ChatOpenAI

from .prompts import ANALYZE_PROMPT, FORMAT_PROMPT, PLAN_PROMPT, REFLECT_PROMPT
from .streaming import emit_token
from .tools import search_web


def get_llm():
    return ChatOpenAI(model="gpt-4o", temperature=0.1)


def _parse_json(content: str):
    """Best-effort extraction of a JSON value from an LLM response.

    Handles bare JSON as well as ```json fenced blocks.
    """
    content = content.strip()
    if content.startswith("```"):
        # Drop the opening fence (``` or ```json) and the trailing fence.
        content = content.split("```")[1]
        if content.lstrip().startswith("json"):
            content = content.lstrip()[4:]
    return json.loads(content.strip())


def plan_node(state: dict) -> dict:
    llm = get_llm()
    question = state["question"]

    response = llm.invoke(PLAN_PROMPT.format(question=question))
    sub_queries = _parse_json(response.content)

    return {
        **state,
        "sub_queries": sub_queries,
        "pending_queries": sub_queries,
        "executed_queries": [],
        "stage": "planning",
        "stage_detail": f"Planning: broke the question into {len(sub_queries)} sub-queries",
    }


def search_node(state: dict) -> dict:
    """Execute the pending queries and accumulate results across rounds."""
    pending = state.get("pending_queries") or state.get("sub_queries", [])
    all_results = list(state.get("search_results", []))
    all_sources = list(state.get("sources", []))
    executed = list(state.get("executed_queries", []))

    for query in pending:
        if query in executed:
            continue
        try:
            response = search_web(query)
            results = response.get("results", [])
            all_results.append({"query": query, "results": results})
            for r in results:
                source = {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:200],
                }
                if source not in all_sources:
                    all_sources.append(source)
        except Exception:
            all_results.append({"query": query, "results": [], "error": "Search failed"})
        executed.append(query)

    return {
        **state,
        "search_results": all_results,
        "sources": all_sources,
        "executed_queries": executed,
        "pending_queries": [],
        "stage": "searching",
        "stage_detail": f"Searched the web ({len(executed)} queries run, {len(all_sources)} sources gathered)...",
    }


def reflect_node(state: dict) -> dict:
    """Decide whether the gathered evidence is sufficient, or plan follow-ups.

    This is what makes the pipeline an *agent*: it inspects its own progress
    and chooses whether to dig deeper, within a bounded number of rounds.
    """
    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", 2)

    # Hard safety cap: never loop past the budget, regardless of the verdict.
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
        # If reflection fails to parse, fail safe: treat evidence as sufficient.
        verdict = {"sufficient": True, "gaps": [], "new_queries": []}

    sufficient = bool(verdict.get("sufficient", True))
    gaps = verdict.get("gaps", []) or []
    new_queries = [] if sufficient else (verdict.get("new_queries", []) or [])

    # Never re-run a query we've already executed.
    new_queries = [q for q in new_queries if q not in executed]

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
        "pending_queries": new_queries,
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
        results_text += f"\n### Query: {item['query']}\n"
        for r in item.get("results", []):
            results_text += f"- **{r.get('title', 'N/A')}**: {r.get('content', 'N/A')[:500]}\n"

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

    sources_text = "\n".join(
        f"- [{s['title']}]({s['url']})" for s in sources if s.get("url")
    )

    prompt = FORMAT_PROMPT.format(
        question=question, analysis=analysis, sources=sources_text
    )

    # Stream the report token-by-token so the caller can forward each delta to
    # the UI in real time. We accumulate the full text to persist at the end.
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

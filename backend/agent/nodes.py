import json

from langchain_openai import ChatOpenAI

from .prompts import ANALYZE_PROMPT, FORMAT_PROMPT, PLAN_PROMPT
from .tools import search_web


def get_llm():
    return ChatOpenAI(model="gpt-4o", temperature=0.1)


def plan_node(state: dict) -> dict:
    llm = get_llm()
    question = state["question"]

    response = llm.invoke(PLAN_PROMPT.format(question=question))
    content = response.content.strip()

    # Parse JSON array from response
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    sub_queries = json.loads(content)

    return {**state, "sub_queries": sub_queries, "stage": "planning"}


def search_node(state: dict) -> dict:
    sub_queries = state["sub_queries"]
    all_results = []
    all_sources = []

    for query in sub_queries:
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

    return {**state, "search_results": all_results, "sources": all_sources, "stage": "searching"}


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

    return {**state, "analysis": response.content, "stage": "analyzing"}


def format_node(state: dict) -> dict:
    llm = get_llm()
    question = state["question"]
    analysis = state["analysis"]
    sources = state["sources"]

    sources_text = "\n".join(
        f"- [{s['title']}]({s['url']})" for s in sources if s.get("url")
    )

    response = llm.invoke(
        FORMAT_PROMPT.format(
            question=question, analysis=analysis, sources=sources_text
        )
    )

    return {**state, "report": response.content, "stage": "formatting"}

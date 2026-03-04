from langgraph.graph import END, StateGraph

from .nodes import analyze_node, format_node, plan_node, search_node

# Define state as a TypedDict for LangGraph
from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    question: str
    sub_queries: list[str]
    search_results: list[dict[str, Any]]
    sources: list[dict[str, str]]
    analysis: str
    report: str
    stage: str


def build_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("search", search_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("format", format_node)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "search")
    workflow.add_edge("search", "analyze")
    workflow.add_edge("analyze", "format")
    workflow.add_edge("format", END)

    return workflow.compile()


def run_research(question: str, status_callback=None) -> dict:
    graph = build_graph()
    initial_state = {"question": question}

    final_state = None
    for event in graph.stream(initial_state):
        for node_name, node_state in event.items():
            if status_callback and "stage" in node_state:
                status_callback(node_state["stage"], node_name)
            final_state = node_state

    return final_state

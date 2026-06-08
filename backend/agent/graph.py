from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from .nodes import analyze_node, format_node, plan_node, reflect_node, search_node
from .streaming import set_token_sink
from .tools import set_document_retriever


class ResearchState(TypedDict, total=False):
    question: str
    sub_queries: list[str]          # every sub-query generated (plan + follow-ups)
    pending_queries: list[str]      # queries waiting to be searched this round
    executed_queries: list[str]     # queries already searched (dedup guard)
    search_results: list[dict[str, Any]]
    sources: list[dict[str, str]]
    knowledge_gaps: list[str]       # gaps the reflection step identified
    new_queries: list[str]          # follow-ups proposed by the last reflection
    analysis: str
    report: str
    iteration: int                  # how many reflection rounds have run
    max_iterations: int             # hard cap on reflection rounds (cost guard)
    is_sufficient: bool             # reflection verdict on evidence completeness
    has_documents: bool             # whether the user has a searchable corpus
    stage: str
    stage_detail: str


def should_continue(state: ResearchState) -> str:
    """Conditional edge: loop back to search for more evidence, or synthesize.

    The agent keeps researching only while the reflection step says the
    evidence is insufficient AND there are concrete follow-up queries to run
    AND we are still within the iteration budget.
    """
    if state.get("is_sufficient"):
        return "analyze"
    if not state.get("pending_queries"):
        return "analyze"
    if state.get("iteration", 0) >= state.get("max_iterations", 2):
        return "analyze"
    return "search"


def build_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("search", search_node)
    workflow.add_node("reflect", reflect_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("format", format_node)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "search")
    workflow.add_edge("search", "reflect")
    # The reflection step decides: search again (loop) or move on to analysis.
    workflow.add_conditional_edges(
        "reflect",
        should_continue,
        {"search": "search", "analyze": "analyze"},
    )
    workflow.add_edge("analyze", "format")
    workflow.add_edge("format", END)

    return workflow.compile()


def run_research(
    question: str,
    status_callback=None,
    token_callback=None,
    retriever=None,
    has_documents: bool = False,
    max_iterations: int = 2,
) -> dict:
    """Run the agentic research graph.

    Args:
        question: the user's research question.
        status_callback: optional callable(stage, detail, meta) invoked at each
            node so the caller can stream progress (e.g. over a WebSocket).
        token_callback: optional callable(delta) invoked for each token of the
            final report as it is generated, enabling live streaming to the UI.
        retriever: optional callable(query) -> list[source dict] that searches
            the requesting user's documents. Injected so the agent stays
            decoupled from Django/DB.
        has_documents: whether the user has a searchable document corpus; when
            True the planner may route sub-queries to document retrieval.
        max_iterations: hard cap on reflection/search loops (cost + latency guard).
    """
    set_token_sink(token_callback)
    set_document_retriever(retriever)
    graph = build_graph()
    initial_state: ResearchState = {
        "question": question,
        "iteration": 0,
        "max_iterations": max_iterations,
        "has_documents": has_documents,
        "sub_queries": [],
        "pending_queries": [],
        "executed_queries": [],
        "search_results": [],
        "sources": [],
    }

    final_state: dict = dict(initial_state)
    for event in graph.stream(initial_state):
        for node_name, node_state in event.items():
            if not node_state:
                continue
            final_state.update(node_state)
            if status_callback and node_state.get("stage"):
                status_callback(
                    node_state["stage"],
                    node_state.get("stage_detail", ""),
                    {
                        "node": node_name,
                        "iteration": node_state.get("iteration", 0),
                    },
                )

    return final_state

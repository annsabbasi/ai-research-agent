import contextvars
import os
from typing import Callable, List, Optional

from tavily import TavilyClient

# Document retrieval is injected per-run (bound to the requesting user) so the
# agent package stays decoupled from Django/DB and remains unit-testable.
_doc_retriever: contextvars.ContextVar[Optional[Callable[[str], List[dict]]]] = (
    contextvars.ContextVar("document_retriever", default=None)
)


def set_document_retriever(retriever: Optional[Callable[[str], List[dict]]]) -> None:
    """Register the callable used to retrieve from the user's documents (or None)."""
    _doc_retriever.set(retriever)


def search_documents(query: str) -> List[dict]:
    """Retrieve relevant chunks from the user's documents, if a retriever is set."""
    retriever = _doc_retriever.get()
    if retriever is None:
        return []
    try:
        return retriever(query) or []
    except Exception:
        # Retrieval failures must not abort the run; the web path still works.
        return []


def get_tavily_client():
    return TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))


def search_web(query: str, max_results: int = 5) -> dict:
    client = get_tavily_client()
    response = client.search(query, search_depth="advanced", max_results=max_results)
    return response

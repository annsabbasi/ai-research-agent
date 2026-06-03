"""Token-streaming plumbing for the research agent.

The report is generated deep inside `format_node`, but the thing that wants the
tokens (the Celery task pushing them over a WebSocket) lives outside the graph.
We bridge the two with a context-local "sink" so nodes can emit tokens without
the graph having to thread a callback through every node's state.

A ContextVar is used (rather than a module global) so concurrent runs in the
same process — e.g. a Celery worker with concurrency > 1 using threads — never
cross-talk: each run sets its own sink in its own context.
"""

import contextvars
from typing import Callable, Optional

_token_sink: contextvars.ContextVar[Optional[Callable[[str], None]]] = (
    contextvars.ContextVar("research_token_sink", default=None)
)


def set_token_sink(callback: Optional[Callable[[str], None]]) -> None:
    """Register the callback that receives streamed token deltas (or None)."""
    _token_sink.set(callback)


def emit_token(text: str) -> None:
    """Send a token delta to the active sink, if one is registered.

    Never raises: a streaming/transport failure must not abort the research run.
    """
    if not text:
        return
    sink = _token_sink.get()
    if sink is None:
        return
    try:
        sink(text)
    except Exception:
        # Streaming is best-effort; the full report is still saved at the end.
        pass

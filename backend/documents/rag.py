"""Chunking and embedding utilities for the RAG corpus.

Kept deliberately free of Django/DB imports at module load so the pure logic
(text splitting) is unit-testable in isolation. Anything that needs settings or
the network is imported lazily inside the function that uses it.
"""

import html as _html
import re
from typing import Iterable, List, Optional

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
DEFAULT_SEPARATORS = ("\n\n", "\n", ". ", " ", "")


# --------------------------------------------------------------------------- #
# Chunking
# --------------------------------------------------------------------------- #
def _recursive_split(text: str, chunk_size: int, separators: List[str]) -> List[str]:
    """Break text into atomic pieces, each <= chunk_size where possible.

    Tries separators from coarse (paragraph) to fine (word), falling back to a
    hard character cut so no piece ever exceeds chunk_size.
    """
    if len(text) <= chunk_size:
        return [text] if text else []

    separator = ""
    remaining: List[str] = []
    for i, sep in enumerate(separators):
        if sep == "":
            separator = ""
            remaining = []
            break
        if sep in text:
            separator = sep
            remaining = separators[i + 1:]
            break

    if separator == "":
        # No usable separator left: cut on character boundaries.
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    pieces: List[str] = []
    for part in text.split(separator):
        part = part.strip()
        if not part:
            continue
        if len(part) <= chunk_size:
            pieces.append(part)
        else:
            pieces.extend(_recursive_split(part, chunk_size, remaining))
    return pieces


def _merge(pieces: List[str], chunk_size: int, overlap: int) -> List[str]:
    """Greedily pack atomic pieces into chunks, carrying a character overlap."""
    chunks: List[str] = []
    current = ""

    for piece in pieces:
        candidate = piece if not current else f"{current} {piece}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        # Seed the next chunk with the tail of the previous one so context
        # spanning a boundary is not lost between adjacent chunks.
        if overlap and chunks:
            tail = chunks[-1][-overlap:].strip()
            seeded = f"{tail} {piece}".strip()
            current = seeded if len(seeded) <= chunk_size else piece
        else:
            current = piece

    if current:
        chunks.append(current)
    return chunks


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
) -> List[str]:
    """Split text into overlapping, boundary-aware chunks for embedding."""
    text = (text or "").strip()
    if not text:
        return []
    overlap = max(0, min(overlap, chunk_size - 1))
    pieces = _recursive_split(text, chunk_size, list(separators))
    return _merge(pieces, chunk_size, overlap)


# --------------------------------------------------------------------------- #
# Embeddings
# --------------------------------------------------------------------------- #
def _embedding_model_name() -> str:
    try:
        from django.conf import settings

        return getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small")
    except Exception:
        return "text-embedding-3-small"


def get_embedder(model: Optional[str] = None):
    """Build an OpenAI embeddings client (lazy import; needs OPENAI_API_KEY)."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model=model or _embedding_model_name())


def embed_texts(texts: List[str], embedder=None) -> List[List[float]]:
    """Embed a batch of documents. `embedder` is injectable for testing."""
    if not texts:
        return []
    embedder = embedder or get_embedder()
    return embedder.embed_documents(list(texts))


def embed_query(text: str, embedder=None) -> List[float]:
    """Embed a single query string. `embedder` is injectable for testing."""
    embedder = embedder or get_embedder()
    return embedder.embed_query(text)


# --------------------------------------------------------------------------- #
# Text extraction
# --------------------------------------------------------------------------- #
_SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
_TAG_RE = re.compile(r"(?s)<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(raw: str) -> str:
    """Best-effort plain-text extraction from an HTML string.

    Drops <script>/<style> blocks and tags, unescapes entities, and collapses
    whitespace. Good enough for embedding; not a full DOM parser.
    """
    if not raw:
        return ""
    raw = _SCRIPT_STYLE_RE.sub(" ", raw)
    raw = _TAG_RE.sub(" ", raw)
    return _WS_RE.sub(" ", _html.unescape(raw)).strip()


def fetch_url_text(url: str, timeout: int = 20) -> str:
    """Fetch a URL and return its extracted plain text (network call)."""
    import urllib.request

    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (ai-research-agent)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
    return strip_html(raw)

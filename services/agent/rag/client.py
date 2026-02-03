"""
RAG (Retrieval-Augmented Generation) client – STUB
=====================================================
Returns empty context today.  Replace with real vector-search later.

Future implementation steps:
  1. Choose a vector store (pgvector, Chroma, Weaviate …).
  2. Ingest maritime documentation / manuals → embed → store.
  3. On each event, embed the query and retrieve the top-K chunks.
  4. Return those chunks so the LLM prompt is grounded.

TODO: implement vector-DB retrieval here.
"""

from typing import List
from dataclasses import dataclass


@dataclass
class RAGDocument:
    """One retrieved chunk of context."""
    title:   str
    content: str
    source:  str = "unknown"


# ─── public API ───────────────────────────────────────────
async def retrieve_context(
    event_type:  str,
    sensor_name: str,
    vessel_id:   str,
) -> List[RAGDocument]:
    """
    Retrieve relevant documentation for the given event.

    STUB – always returns an empty list.

    Args:
        event_type:  e.g. 'HIGH_TEMPERATURE'
        sensor_name: e.g. 'engine_temp'
        vessel_id:   e.g. 'vessel_001'
    """
    # TODO: query vector store with an embedding of
    #       f"{event_type} {sensor_name}" and return top-K docs.
    return []


def format_context_for_prompt(documents: List[RAGDocument]) -> str:
    """
    Serialise retrieved docs into a plain-text block
    that can be pasted into the LLM prompt.
    """
    if not documents:
        return "No relevant documentation available (RAG stub – not yet implemented)."

    parts = []
    for doc in documents:
        parts.append(f"--- {doc.title}  (source: {doc.source}) ---\n{doc.content}")
    return "\n\n".join(parts)

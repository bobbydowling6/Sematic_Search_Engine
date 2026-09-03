"""
Module 7 Project — Semantic Search Engine
==========================================
search.py — query ChromaDB and return ranked results

Import this module into app.py:
    from search import search, get_collection_stats
"""

from pathlib import Path
import chromadb

# ── Configuration (must match ingest.py) ─────────────────────────────────────
CHROMA_PATH = Path(__file__).resolve().parent / "chroma_data"
COLLECTION_NAME = "semantic_search"
MODEL_NAME = "all-MiniLM-L6-v2"


def get_collection():
    """Return the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def search(
    query: str,
    n_results: int = 5,
    sources: list[str] = None,
    distance_threshold: float = None,
) -> list[dict]:
    """
    Search the ChromaDB collection and return ranked results.

    Args:
        query:              Natural language search query.
        n_results:          Maximum number of results to return.
        sources:            If provided, only return chunks from these filenames.
        distance_threshold: If provided, exclude results with distance above this
                            value (lower = more similar).

    Returns:
        List of result dicts sorted by distance ascending (best first):
            {
                "text":        str,
                "source":      str,
                "chunk_index": int,
                "distance":    float,
                "score":       float,  # 1 - distance
            }
        Returns [] for empty queries or if the collection has no documents.
    """
    if not query or not query.strip():
        return []
    if n_results <= 0:
        return []
    if sources is not None and not sources:
        return []

    collection = get_collection()
    total_chunks = collection.count()
    if total_chunks == 0:
        return []

    query_kwargs = {
        "query_texts": [query],
        "n_results": min(n_results, total_chunks),
    }
    if sources is not None:
        query_kwargs["where"] = {"source": {"$in": sources}}

    raw_results = collection.query(**query_kwargs)
    documents = raw_results.get("documents", [[]])[0] or []
    metadatas = raw_results.get("metadatas", [[]])[0] or []
    distances = raw_results.get("distances", [[]])[0] or []

    results = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        if distance_threshold is not None and distance > distance_threshold:
            continue

        metadata = metadata or {}
        results.append({
            "text": text,
            "source": metadata.get("source", ""),
            "chunk_index": int(metadata.get("chunk_index", 0)),
            "distance": float(distance),
            "score": 1 - float(distance),
        })

    return results


def get_collection_stats() -> dict:
    """
    Return basic stats about the indexed collection.

    Returns:
        {
            "total_chunks":   int,
            "unique_sources": int,
            "source_names":   list[str],
        }
    """
    collection = get_collection()
    metadatas = collection.get(include=["metadatas"]).get("metadatas", []) or []
    source_names = sorted({metadata.get("source", "") for metadata in metadatas if metadata})
    source_names = [source for source in source_names if source]

    return {
        "total_chunks": collection.count(),
        "unique_sources": len(source_names),
        "source_names": source_names,
    }
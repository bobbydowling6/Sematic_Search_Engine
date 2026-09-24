"""Query a chunk-size-specific ChromaDB index."""

import os
from pathlib import Path
import chromadb

# Ensure CHROMA_PATH aligns with ingest.py and app.py
ROOT_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = ROOT_DIR / "storage" / "chroma_data"
DEFAULT_COLLECTION_NAME = "semantic_search_500"


def get_collection(collection_name: str | None = None):
    """Retrieves or creates a ChromaDB collection safely."""
    # Ensure directory structure exists
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    name = collection_name or os.environ.get("CHROMA_COLLECTION", DEFAULT_COLLECTION_NAME)
    return client.get_or_create_collection(name=name)


def search(
    query: str,
    n_results: int = 5,
    sources: list[str] | None = None,
    distance_threshold: float | None = None,
    collection_name: str | None = None,
) -> list[dict]:
    """Queries ChromaDB using semantic vector search with optional metadata filters."""
    if not query or not query.strip() or n_results <= 0 or sources == []:
        return []

    try:
        collection = get_collection(collection_name)
        total_chunks = collection.count()
        if total_chunks == 0:
            return []

        query_kwargs = {"query_texts": [query], "n_results": min(n_results, total_chunks)}

        # ChromaDB operator handling for single vs multiple sources
        if sources:
            if len(sources) == 1:
                query_kwargs["where"] = {"source": sources[0]}
            else:
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
            
            # Safe conversion of chunk_index (whether stored as int or str)
            raw_index = metadata.get("chunk_index", 0)
            try:
                chunk_index = int(raw_index)
            except (ValueError, TypeError):
                chunk_index = 0

            results.append({
                "text": text,
                "source": metadata.get("source", "Unknown"),
                "chunk_index": chunk_index,
                "distance": float(distance),
                "score": 1 - float(distance),
            })

        return results

    except Exception as e:
        print(f"Error executing search query: {e}")
        return []


def get_collection_stats(collection_name: str | None = None) -> dict:
    """Returns summary metrics and source names for the index."""
    try:
        collection = get_collection(collection_name)
        total_chunks = collection.count()

        if total_chunks == 0:
            return {
                "total_chunks": 0,
                "unique_sources": 0,
                "source_names": [],
            }

        metadatas = collection.get(include=["metadatas"]).get("metadatas", []) or []
        source_names = sorted({m.get("source", "") for m in metadatas if m and "source" in m})
        source_names = [s for s in source_names if s]

        return {
            "total_chunks": total_chunks,
            "unique_sources": len(source_names),
            "source_names": source_names,
        }

    except Exception as e:
        print(f"Error fetching collection stats: {e}")
        return {
            "total_chunks": 0,
            "unique_sources": 0,
            "source_names": [],
        }
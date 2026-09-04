"""Query a chunk-size-specific ChromaDB index."""

import os
from pathlib import Path

import chromadb


CHROMA_PATH = Path(__file__).resolve().parent / "chroma_data"
DEFAULT_COLLECTION_NAME = "semantic_search_500"


def get_collection(collection_name: str | None = None):
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
    if not query or not query.strip() or n_results <= 0 or sources == []:
        return []

    collection = get_collection(collection_name)
    total_chunks = collection.count()
    if total_chunks == 0:
        return []

    query_kwargs = {"query_texts": [query], "n_results": min(n_results, total_chunks)}
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


def get_collection_stats(collection_name: str | None = None) -> dict:
    collection = get_collection(collection_name)
    metadatas = collection.get(include=["metadatas"]).get("metadatas", []) or []
    source_names = sorted({metadata.get("source", "") for metadata in metadatas if metadata})
    source_names = [source for source in source_names if source]
    return {
        "total_chunks": collection.count(),
        "unique_sources": len(source_names),
        "source_names": source_names,
    }
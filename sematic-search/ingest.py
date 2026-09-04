"""Load the course documents into one or more chunk-size indexes."""

import argparse
from pathlib import Path

import chromadb


DOCS_DIR = Path(__file__).resolve().parent.parent / "storage" / "docs"
CHROMA_PATH = Path(__file__).resolve().parent.parent / "storage" / "chroma_data"
COLLECTION_PREFIX = "semantic_search"
DEFAULT_CHUNK_SIZES = (200, 500)
DEFAULT_OVERLAP = 50


def fixed_chunks(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping fixed-size chunks."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap must be smaller than size")

    step = size - overlap
    return [
        text[start:min(start + size, len(text))].strip()
        for start in range(0, len(text), step)
        if text[start:min(start + size, len(text))].strip()
    ]


def load_documents(docs_dir: Path) -> list[dict[str, str]]:
    documents = []
    for path in sorted(docs_dir.iterdir()):
        if path.suffix in {".txt", ".md"}:
            documents.append({"content": path.read_text(encoding="utf-8"), "source": path.name})
    return documents


def collection_name(chunk_size: int) -> str:
    return f"{COLLECTION_PREFIX}_{chunk_size}"


def ingest(chunk_size: int, overlap: int = DEFAULT_OVERLAP) -> int:
    """Rebuild and populate the persistent index for one chunk size."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    name = collection_name(chunk_size)
    try:
        client.delete_collection(name)
    except Exception:
        pass
    collection = client.create_collection(name=name)

    chunks = []
    metadatas = []
    ids = []
    documents = load_documents(DOCS_DIR)
    for document in documents:
        for index, chunk in enumerate(fixed_chunks(document["content"], chunk_size, overlap)):
            chunks.append(chunk)
            metadatas.append({
                "source": document["source"],
                "chunk_index": str(index),
                "chunk_size": str(chunk_size),
            })
            ids.append(f"{document['source']}_{chunk_size}_{index}")

    collection.upsert(documents=chunks, metadatas=metadatas, ids=ids)
    print(f"{name}: indexed {len(chunks)} chunks from {len(documents)} documents")
    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index docs/ into ChromaDB")
    parser.add_argument("--chunk-size", type=int, choices=range(1, 2001))
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP)
    args = parser.parse_args()
    sizes = (args.chunk_size,) if args.chunk_size else DEFAULT_CHUNK_SIZES
    for size in sizes:
        ingest(size, args.overlap)
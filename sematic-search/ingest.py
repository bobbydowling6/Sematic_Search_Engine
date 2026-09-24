"""Load the course documents into one or more chunk-size indexes."""

import argparse
from pathlib import Path
import chromadb

DOCS_DIR = Path(__file__).resolve().parent.parent / "storage" / "docs"
CHROMA_PATH = Path(__file__).resolve().parent.parent / "storage" / "chroma_data"
COLLECTION_PREFIX = "semantic_search"
DEFAULT_CHUNK_SIZES = (200, 500)
DEFAULT_OVERLAP = 50
BATCH_SIZE = 1000  # Safe batch limit for ChromaDB inserts


def fixed_chunks(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping fixed-size chunks."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap must be smaller than size")

    step = size - overlap
    chunks = []
    for start in range(0, len(text), step):
        chunk = text[start : min(start + size, len(text))].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def load_documents(docs_dir: Path) -> list[dict[str, str]]:
    """Safely load markdown and text files from the docs directory."""
    documents = []
    if not docs_dir.exists():
        print(f"Warning: Directory '{docs_dir}' does not exist.")
        return documents

    for path in sorted(docs_dir.iterdir()):
        if path.is_file() and path.suffix in {".txt", ".md"}:
            try:
                content = path.read_text(encoding="utf-8")
                if content.strip():
                    documents.append({"content": content, "source": path.name})
            except Exception as e:
                print(f"Error reading {path.name}: {e}")
                
    return documents


def collection_name(chunk_size: int) -> str:
    return f"{COLLECTION_PREFIX}_{chunk_size}"


def ingest(chunk_size: int, overlap: int = DEFAULT_OVERLAP) -> int:
    """Rebuild and populate the persistent index for one chunk size."""
    CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    
    if not documents:
        print(f"No documents found in {DOCS_DIR}")
        return 0

    for document in documents:
        source_name = document["source"]
        for index, chunk in enumerate(fixed_chunks(document["content"], chunk_size, overlap)):
            chunks.append(chunk)
            metadatas.append({
                "source": source_name,
                "chunk_index": index,      # Stored as int for numeric metadata querying
                "chunk_size": chunk_size,   # Stored as int
            })
            # Sanitize filename for ID safety
            safe_source = source_name.replace(" ", "_")
            ids.append(f"{safe_source}_{chunk_size}_{index}")

    # Batch upserts to stay under ChromaDB batch limits
    for i in range(0, len(chunks), BATCH_SIZE):
        collection.upsert(
            documents=chunks[i : i + BATCH_SIZE],
            metadatas=metadatas[i : i + BATCH_SIZE],
            ids=ids[i : i + BATCH_SIZE],
        )

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
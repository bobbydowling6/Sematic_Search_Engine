"""
Module 7 Project — Semantic Search Engine
==========================================
ingest.py — document loading, chunking, and ChromaDB storage

Run with:
    python ingest.py
    python ingest.py --chunk-size 200 --overlap 50
"""
from multiprocessing import util
import os
import argparse
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import re

# ── Configuration ─────────────────────────────────────────────────────────────
DOCS_DIR = Path("../storage/docs")
CHROMA_PATH = Path("../storage/chroma_data")
COLLECTION_NAME = "semantic_search"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZES = 150, 300, 600
DEFAULT_OVERLAP = 50

model = SentenceTransformer('all-MiniLM-L6-v2')

def fixed_small_chunks(text, size=150, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap  # advance by a fixed step so this always terminates
    return [c for c in chunks if c]

def fixed_medium_chunks(text, size=300, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap  # advance by a fixed step so this always terminates
    return [c for c in chunks if c]

def fixed_large_chunks(text, size=600, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap  # advance by a fixed step so this always terminates
    return [c for c in chunks if c]

strategies = {
    "fixed_small": fixed_small_chunks,
    "fixed_medium": fixed_medium_chunks,
    "fixed_large": fixed_large_chunks,
}

for name, chunks in strategies.items():
    sizes = [len(c) for c in chunks]
    print(f"{name}: {len(chunks)} chunks, avg {sum(sizes)//len(sizes)} chars")

query_1 = "How does FastAPI validate data?"
print(f"Query: '{query_1}'")
query_2 = "What is the difference between FastAPI and Flask?"
print(f"Query: '{query_2}'")
query_3 = "How do I deploy a FastAPI app?"
print(f"Query: '{query_3}'")
query_4 = "What are the benefits of using FastAPI?"
print(f"Query: '{query_4}'")
query_5 = "How can I test a FastAPI application?"
print(f"Query: '{query_5}'")

for name, chunks in strategies.items():
    # Embed chunks
    chunk_embeddings = model.encode(chunks)
    query_embedding = model.encode([query_1, query_2, query_3, query_4, query_5])

    # Find best match
    scores = util.cos_sim(query_embedding, chunk_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    print(f"--- {name} ---")
    print(f"Best score: {best_score:.4f}")
    print(f"Best chunk ({len(chunks[best_idx])} chars):")
    print(f"  '{chunks[best_idx][:120]}...'")


def load_documents(docs_dir: Path) -> list[dict]:
    documents = []
    for filename in os.listdir(docs_dir):
        if filename.endswith(('.txt', '.md')):
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            documents.append({
                "content": content,
                "source": filename,  # Track which file each chunk came from
            })
    return documents

def ingest_documents(directory, collection):
    """Load, chunk, and store documents in ChromaDB."""
    documents = load_documents(directory)
    all_chunks = []
    all_metadatas = []
    all_ids = []

    for doc in documents:
        chunks = paragraph_chunks(doc["content"])  # Your chunking function
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({"source": doc["source"], "chunk_index": str(i)})
            all_ids.append(f"{doc['source']}_{i}")

    collection.upsert(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )
    return len(all_chunks)


    """
    Read all .txt and .md files from docs_dir.

    Returns:
        List of dicts: {"filename": str, "text": str}
    """
    pass


def get_collection(chroma_path: Path, collection_name: str):
    """Create (or retrieve) a persistent ChromaDB collection."""
    pass


def ingest(chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
    """
    Full ingestion pipeline: load → chunk → embed → upsert.

    Each chunk is stored with metadata: source filename, chunk index,
    and the chunk size used — so experiments with different sizes can
    be compared without ambiguity.
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index docs/ into ChromaDB")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--overlap",    type=int, default=DEFAULT_OVERLAP)
    args = parser.parse_args()
    ingest(chunk_size=args.chunk_size, overlap=args.overlap)
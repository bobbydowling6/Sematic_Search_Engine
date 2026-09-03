"""
Module 7 Project — Semantic Search Engine
==========================================
app.py — Streamlit search interface

Run with:
    streamlit run app.py

Make sure you've indexed documents first:
    python ingest.py
"""

import streamlit as st
import os
import sys
from pathlib import Path

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
DOCS_DIR = STORAGE_DIR / "docs"
sys.path.insert(0, str(STORAGE_DIR))

from search import get_collection, get_collection_stats, search

st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")

collection = get_collection()

# --- Document Loading & Chunking ---
def load_and_chunk(directory, chunk_size=400, overlap=50):
    """Load text files and split into chunks."""
    chunks = []
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(('.txt', '.md')):
            continue
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by paragraphs (double newline)
        paragraphs = [p.strip() for p in content.split('\\n\\n') if p.strip()]

        for i, para in enumerate(paragraphs):
            chunks.append({
                "text": para,
                "source": filename,
                "chunk_id": f"{filename}_{i}",
                "chunk_index": i,
            })
    return chunks

# --- Sidebar: Ingestion Controls ---
with st.sidebar:
    st.title("📁 Document Manager")

    if st.button("🔄 Re-index Documents"):
        chunks = load_and_chunk(DOCS_DIR)
        if chunks:
            collection.upsert(
                documents=[c["text"] for c in chunks],
                metadatas=[{"source": c["source"], "chunk_index": str(c["chunk_index"])} for c in chunks],
                ids=[c["chunk_id"] for c in chunks],
            )
            st.success(f"Indexed {len(chunks)} chunks from {len(set(c['source'] for c in chunks))} files")
        else:
            st.warning("No .txt or .md files found in docs/ folder")

    collection_stats = get_collection_stats()
    st.metric("Indexed chunks", collection_stats["total_chunks"])
    st.metric("Source files", collection_stats["unique_sources"])

    st.divider()
    n_results = st.slider("Results to show", 1, 10, 5)
    selected_sources = st.multiselect(
        "Filter by source file",
        options=collection_stats["source_names"],
    )
    distance_threshold = st.slider("Maximum distance", 0.0, 2.0, 1.0, 0.05)

# --- Main Search Interface ---
st.title("🔍 Semantic Search")
st.write("Search your course documents by meaning, not just keywords.")

query = st.text_input("Enter your search query", placeholder="How does authentication work?")

if query.strip():
    results = search(
        query,
        n_results=n_results,
        sources=selected_sources or None,
        distance_threshold=distance_threshold,
    )

    if results:
        st.subheader(f"Top {len(results)} Results")

        for result in results:
            distance = result["distance"]

            if distance < 0.5:
                relevance = "🟢 High"
            elif distance < 1.0:
                relevance = "🟡 Medium"
            else:
                relevance = "🔴 Low"

            with st.container():
                col_meta, col_score = st.columns([3, 1])
                with col_meta:
                    st.write(f"**{result['source']}** — chunk {result['chunk_index']}")
                with col_score:
                    st.write(f"{relevance} (dist: {distance:.3f})")
                st.write(result["text"])
                st.divider()
    else:
        st.info("No results matched the selected distance threshold and source filters.")

elif collection_stats["total_chunks"] == 0:
    st.info("👈 Click 'Re-index Documents' in the sidebar to load your documents first.")

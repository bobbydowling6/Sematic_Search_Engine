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
import chromadb
import os
from search import search, get_collection_stats
from ingest import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP

st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")

# --- ChromaDB Setup ---
@st.cache_resource  # Cache the client so it persists across re-runs
def get_collection():
    client = chromadb.PersistentClient(path="./search_db")
    return client.get_or_create_collection(name="course_docs")

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
        chunks = load_and_chunk("docs")
        if chunks:
            collection.upsert(
                documents=[c["text"] for c in chunks],
                metadatas=[{"source": c["source"], "chunk_index": str(c["chunk_index"])} for c in chunks],
                ids=[c["chunk_id"] for c in chunks],
            )
            st.success(f"Indexed {len(chunks)} chunks from {len(set(c['source'] for c in chunks))} files")
        else:
            st.warning("No .txt or .md files found in docs/ folder")

    st.metric("Documents in DB", collection.count())

    st.divider()
    n_results = st.slider("Results to show", 1, 10, 5)

# --- Main Search Interface ---
st.title("🔍 Semantic Search")
st.write("Search your course documents by meaning, not just keywords.")

query = st.text_input("Enter your search query", placeholder="How does authentication work?")

if query and collection.count() > 0:
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )

    st.subheader(f"Top {len(results['documents'][0])} Results")

    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        metadata = results['metadatas'][0][i]
        distance = results['distances'][0][i]

        # Color-code by relevance
        if distance < 0.5:
            relevance = "🟢 High"
        elif distance < 1.0:
            relevance = "🟡 Medium"
        else:
            relevance = "🔴 Low"

        with st.container():
            col_meta, col_score = st.columns([3, 1])
            with col_meta:
                st.write(f"**{metadata['source']}** — chunk {metadata['chunk_index']}")
            with col_score:
                st.write(f"{relevance} (dist: {distance:.3f})")
            st.write(doc)
            st.divider()

elif collection.count() == 0:
    st.info("👈 Click 'Re-index Documents' in the sidebar to load your documents first.")

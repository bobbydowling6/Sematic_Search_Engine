import sys
import os
from pathlib import Path
import streamlit as st

# --- Path Configuration ---
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd()

STORAGE_DIR = SCRIPT_DIR.parent / "storage"
DOCS_DIR = STORAGE_DIR / "docs"

if str(STORAGE_DIR) not in sys.path:
    sys.path.insert(0, str(STORAGE_DIR))

from ingest import ingest as ingest_documents
from search import get_collection_stats, search

st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")

# --- Sidebar: Ingestion Controls ---
with st.sidebar:
    st.title("📁 Document Manager")

    if st.button("🔄 Re-index Documents"):
        with st.spinner("Indexing documents..."):
            chunk_count = ingest_documents(500)
        st.success(f"Indexed {chunk_count} chunks using the 500-character index")
        st.rerun()  # Force Streamlit to rerun and refresh collection stats immediately

    # Safely fetch collection stats
    collection_stats = get_collection_stats() or {
        "total_chunks": 0,
        "unique_sources": 0,
        "source_names": [],
    }

    st.metric("Indexed chunks", collection_stats.get("total_chunks", 0))
    st.metric("Source files", collection_stats.get("unique_sources", 0))

    st.divider()
    n_results = st.slider("Results to show", 1, 10, 5)
    
    # Safe fallback for multiselect options
    source_options = collection_stats.get("source_names") or []
    selected_sources = st.multiselect(
        "Filter by source file",
        options=source_options,
    )
    distance_threshold = st.slider("Maximum distance", 0.0, 2.0, 1.0, 0.05)

# --- Main Search Interface ---
st.title("🔍 Semantic Search")
st.write("Search your course documents by meaning, not just keywords.")

query = st.text_input("Enter your search query", placeholder="What is a SQL Database?")

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
            distance = result.get("distance", 0.0)

            if distance < 0.5:
                relevance = "🟢 High"
            elif distance < 1.0:
                relevance = "🟡 Medium"
            else:
                relevance = "🔴 Low"

            with st.container():
                col_meta, col_score = st.columns([3, 1])
                with col_meta:
                    st.write(f"**{result.get('source', 'Unknown')}** — chunk {result.get('chunk_index', 'N/A')}")
                with col_score:
                    st.write(f"{relevance} (dist: {distance:.3f})")
                st.write(result.get("text", ""))
                st.divider()
    else:
        st.info("No results matched the selected distance threshold and source filters.")

elif collection_stats.get("total_chunks", 0) == 0:
    st.info("👈 Click 'Re-index Documents' in the sidebar to load your documents first.")
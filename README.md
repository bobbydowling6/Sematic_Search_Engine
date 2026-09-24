# Semantic Search Engine

A Streamlit-based semantic search application for course documents stored in `storage/docs`. Documents are processed, chunked, and indexed into ChromaDB for vector-based semantic retrieval.

## Project Architecture

```
.
├── sematic-search/
│   ├── app.py          # Streamlit UI with auto-refresh state and result visualization
│   └── ingest.py       # Batched document chunking, metadata extraction, and indexing
└── storage/
    ├── search.py       # Robust ChromaDB query engine with single/multi-source filtering
    ├── evaluate.py     # Evaluation framework calculating Precision@3 across chunk sizes
    ├── docs/           # Source .txt and .md document files
    ├── chroma_data/    # Persistent ChromaDB vector database files
    └── requirements.txt
```

---

## Technical Features & Improvements

* **Batch Ingestion**: `ingest.py` chunks data and performs batched upserts (1,000 documents per batch) to prevent payload errors on large document collections.
* **Native Numeric Metadata**: Chunk indices are saved as native integers in ChromaDB to enable precise metadata filtering and numeric sorting.
* **Resilient UI Reruns**: `app.py` triggers `st.rerun()` upon re-indexing to force immediate UI state updates and uses defensive dictionary getters to handle fresh/empty indexes smoothly.
* **Corrected Precision Calculation**: `evaluate.py` accurately evaluates Precision@3 against fixed $k=3$ rank bounds and outputs aggregate Mean Precision@3 (mP@3) across collections.
* **Smart Filter Handling**: `search.py` automatically adapts ChromaDB filtering for single source strings vs multi-source lists to prevent query syntax errors.

---

## Setup Instructions

### 1. Set Up Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r storage/requirements.txt
```

### 2. Ingest Course Documents

Generate persistent ChromaDB vector collections using a 50-character overlap:

```bash
python sematic-search/ingest.py
```

This populates two collections:
* `semantic_search_200`: 200-character chunk size
* `semantic_search_500`: 500-character chunk size

To rebuild a specific collection size:

```bash
python sematic-search/ingest.py --chunk-size 500
```

### 3. Launch Streamlit UI

```bash
streamlit run sematic-search/app.py
```

The sidebar provides interactive controls for:
* Re-indexing source documents in real-time
* Adjusting returned result counts ($k$)
* Filtering searches by specific source documents
* Setting maximum cosine distance thresholds

### 4. Run Evaluation Benchmark

Execute the comparative benchmark across both vector collections:

```bash
python storage/evaluate.py
```

---

## Evaluation Benchmark Output

**Relevance Criteria:** Cosine Distance $< 0.80$ (Lower distance represents higher similarity).

| Query | Collection | Rank 1 (Score / Rel) | Rank 2 (Score / Rel) | Rank 3 (Score / Rel) | Precision@3 |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **How does FastAPI validate data?** | 200-char | 0.6597 (R) | 0.7117 (R) | 0.7376 (R) | **1.00** |
|  | 500-char | 0.6766 (R) | 1.1355 (I) | 1.1462 (I) | **0.33** |
| **What is the difference between FastAPI and Flask?** | 200-char | 0.7599 (R) | 0.9793 (I) | 1.0098 (I) | **0.33** |
|  | 500-char | 0.8764 (I) | 1.0912 (I) | 1.2119 (I) | **0.00** |
| **How do I deploy a FastAPI app?** | 200-char | 0.8290 (I) | 0.8614 (I) | 0.9642 (I) | **0.00** |
|  | 500-char | 1.0255 (I) | 1.0333 (I) | 1.2105 (I) | **0.00** |
| **What are the benefits of using FastAPI?** | 200-char | 0.9055 (I) | 0.9887 (I) | 1.1224 (I) | **0.00** |
|  | 500-char | 1.0379 (I) | 1.1563 (I) | 1.1828 (I) | **0.00** |
| **How can I test a FastAPI application?** | 200-char | 0.6470 (R) | 0.7071 (R) | 0.7386 (R) | **1.00** |
|  | 500-char | 0.6853 (R) | 0.8645 (I) | 1.1495 (I) | **0.33** |

### Benchmark Summary

* **200-character Mean Precision@3:** `0.47`
* **500-character Mean Precision@3:** `0.13`
* **Key Finding:** Smaller chunk sizes (200 characters) significantly outperform larger chunks (500 characters) on this dataset by preserving granular context without introducing irrelevant neighboring text.
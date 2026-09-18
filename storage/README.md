# Semantic Search Engine

A Streamlit-based semantic search application for course documents stored in `storage/docs`. Documents are processed, chunked, and indexed into ChromaDB for vector-based semantic retrieval.

## Project Structure

* `sematic-search/app.py`: Streamlit user interface featuring search parameter controls and re-indexing actions.
* `sematic-search/ingest.py`: Document loading, text extraction, character-based chunking, and ChromaDB persistence.
* `storage/search.py`: Core querying module for ChromaDB collections with optional metadata filtering.
* `storage/evaluate.py`: Evaluator comparing search retrieval performance between 200-character and 500-character chunk sizes across five test queries.
* `storage/docs/`: Source `.txt` and `.md` document files.
* `storage/chroma_data/`: Persistent ChromaDB database storage directory.
* `storage/requirements.txt`: Python package dependencies with pinned versions.

---

## Setup Instructions

1. **Clone the repository and set up a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
2. **Install dependencies:**
   pip install -r storage/requirements.txt
3. **Ingest course documents and generate persistent ChromaDB vector collections:**
   python sematic-search/ingest.py

This populates two persistent collections using a 50-character overlap:
semantic_search_200: 200-character chunk size
semantic_search_500: 500-character chunk size
To rebuild a specific collection size:
python sematic-search/ingest.py --chunk-size 500
4. **Launch the Streamlit interface:**
streamlit run sematic-search/app.py

The application queries the semantic_search_200 collection by default. The sidebar offers configuration controls for:
Adjusting returned result counts (k)
Filtering by source module or topic metadata
Applying cosine distance thresholds
Triggering directory re-indexing

5. ** Execute the comparative benchmark across both collections:**
python storage/evaluate.py

### README Markdown Table Output:

| Query | Collection | Rank 1 (Score / Rel) | Rank 2 (Score / Rel) | Rank 3 (Score / Rel) | Precision@3 |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **How does FastAPI validate data?** | 200-char | 0.6597 (R) | 0.7117 (R) | 0.7376 (R) | 1.00 |
|  | 500-char | 0.6766 (R) | 1.1355 (I) | 1.1462 (I) | 0.33 |
| **What is the difference between FastAPI and Flask?** | 200-char | 0.7599 (R) | 0.9793 (I) | 1.0098 (I) | 0.33 |
|  | 500-char | 0.8764 (I) | 1.0912 (I) | 1.2119 (I) | 0.00 |
| **How do I deploy a FastAPI app?** | 200-char | 0.8290 (I) | 0.8614 (I) | 0.9642 (I) | 0.00 |
|  | 500-char | 1.0255 (I) | 1.0333 (I) | 1.2105 (I) | 0.00 |
| **What are the benefits of using FastAPI?** | 200-char | 0.9055 (I) | 0.9887 (I) | 1.1224 (I) | 0.00 |
|  | 500-char | 1.0379 (I) | 1.1563 (I) | 1.1828 (I) | 0.00 |
| **How can I test a FastAPI application?** | 200-char | 0.6470 (R) | 0.7071 (R) | 0.7386 (R) | 1.00 |
|  | 500-char | 0.6853 (R) | 0.8645 (I) | 1.1495 (I) | 0.33 |
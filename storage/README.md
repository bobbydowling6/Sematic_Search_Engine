# Semantic Search Engine

A Streamlit semantic-search application for the course documents in `storage/docs`. Documents are stored in ChromaDB and searched by meaning. The project also includes a Gemini service for generating answers from retrieved chunks.

## Project Structure

- `sematic-search/app.py` - Streamlit user interface and 500-character re-index control
- `sematic-search/ingest.py` - document loading, fixed-size chunking, and ChromaDB ingestion
- `storage/search.py` - ChromaDB retrieval and result filtering
- `storage/evaluate.py` - five-query comparison between chunk-size indexes
- `storage/gemini_service.py` - Gemini answer generation from retrieved results
- `storage/docs/` - source `.txt` and `.md` documents
- `storage/chroma_data/` - persistent ChromaDB data

## Setup

From the project root, use the repository virtual environment:

```bash
./venv/bin/pip install -r storage/requirements.txt
```

For Gemini answers, add an API key to `.streamlit/secrets.toml`:

```toml
Gemini_API_Key = "your-gemini-api-key"
```

The Gemini service also accepts `GEMINI_API_KEY` from the environment. Never commit a real API key to source control.

## Index Documents

Build both experiment indexes with the default command:

```bash
./venv/bin/python sematic-search/ingest.py
```

This creates two separate persistent ChromaDB collections using a 50-character overlap:

- `semantic_search_200`: 200-character chunks
- `semantic_search_500`: 500-character chunks

To rebuild only one size:

```bash
./venv/bin/python sematic-search/ingest.py --chunk-size 500
```

## Run The App

```bash
./venv/bin/streamlit run sematic-search/app.py
```

The app searches the 500-character collection by default. It supports result-count controls, source filters, distance filtering, and re-indexing from the sidebar.

The Gemini service reads the key from Streamlit secrets or the environment. The current `app.py` displays retrieved chunks; to display Gemini-generated answers, import `answer_question` and call it after a non-empty `search()` result.

## Chunk-Size Experiment

The evaluator runs the same five queries against both collections and compares the top-result distance. Lower distance indicates a closer semantic match:

```bash
cd storage
../venv/bin/python evaluate.py
```

## Results

| Query | 200-character distance | 500-character distance | Better size |
| --- | ---: | ---: | --- |
| How does FastAPI validate data? | 0.6597 | 0.6766 | 200 |
| What is the difference between FastAPI and Flask? | 0.7599 | 0.8764 | 200 |
| How do I deploy a FastAPI app? | 0.8290 | 1.0255 | 200 |
| What are the benefits of using FastAPI? | 0.9055 | 1.0379 | 200 |
| How can I test a FastAPI application? | 0.6470 | 0.6853 | 200 |

The 200-character index worked better overall, winning all five queries. Its smaller passages kept retrieved content more focused, while the 500-character chunks included more surrounding content and produced higher distances. The 200-character index contains 139 chunks; the 500-character index contains 49.
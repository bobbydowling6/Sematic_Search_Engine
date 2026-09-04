# Sematic Search Engine

## Chunk-size experiment

The documents are indexed twice with the same 50-character overlap:

```bash
cd storage
../venv/bin/python ../sematic-search/ingest.py
../venv/bin/python evaluate.py
```

The default ingestion command creates two separate persistent collections:

- `semantic_search_200`: 200-character chunks
- `semantic_search_500`: 500-character chunks

The evaluator runs the same five queries against both collections and compares each top result. Lower distance means a better semantic match.

## Results

| Query | 200-character distance | 500-character distance | Better size |
| --- | ---: | ---: | --- |
| How does FastAPI validate data? | 0.6597 | 0.6766 | 200 |
| What is the difference between FastAPI and Flask? | 0.7599 | 0.8764 | 200 |
| How do I deploy a FastAPI app? | 0.8290 | 1.0255 | 200 |
| What are the benefits of using FastAPI? | 0.9055 | 1.0379 | 200 |
| How can I test a FastAPI application? | 0.6470 | 0.6853 | 200 |

The 200-character index worked better overall, winning all five queries. Smaller chunks kept each retrieved passage more focused on the query, while the 500-character chunks included more unrelated surrounding content and produced higher distances. The 200-character index contains 139 chunks; the 500-character index contains 49.
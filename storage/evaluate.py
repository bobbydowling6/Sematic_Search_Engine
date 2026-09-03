"""
Module 7 Project — Semantic Search Engine
==========================================
evaluate.py — precision and recall for your search system

Run with:
    python evaluate.py
    python evaluate.py --n-results 5 --threshold 0.4

Define your evaluation set in EVAL_SET, then run this script against
different index configurations (different chunk sizes) to compare results.
"""

import argparse
from search import search
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "10")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import chromadb

use_semantic_model = os.environ.get("USE_SEMANTIC_MODEL") == "1"
model = None
if use_semantic_model:
    cache_root = Path(os.environ.get("HF_HOME", Path.home() / ".cache/huggingface"))
    model_cache = cache_root / "hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots"
    cached_weights = any(
        weight.stat().st_size > 1_000_000
        for snapshot in model_cache.glob("*")
        for weight in (snapshot / "model.safetensors", snapshot / "pytorch_model.bin")
        if weight.is_file()
    )
    if cached_weights:
        try:
            print("Loading cached semantic model...", flush=True)
            model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as error:
            print(f"Semantic model unavailable: {error}")
    else:
        print("Semantic model weights are not cached; using local TF-IDF embeddings.")        

# Define your evaluation set here.
# Each entry needs a query and the source filenames you expect to be relevant.
# Use at least 5 queries for the chunking experiment.

ids = [
    "doc_01", "doc_02", "doc_03", "doc_04",
        "doc_05", "doc_06", "doc_07", "doc_08",
        "doc_09", "doc_10", "doc_11", "doc_12",
]

documents = {
    "doc_ai_hallucination": "AI hallucinations refer to instances where artificial intelligence systems generate outputs that are not based on real-world data or facts.",
    "doc_machine_learning": "Machine learning is a subset of artificial intelligence that focuses on the development of computer programs that can access data and use it to learn for themselves.",
    "doc_natural_language_processing": "Natural language processing is a field of artificial intelligence that focuses on the interaction between computers and humans through natural language.",
    "doc_sqlalchemy": "SQLAlchemy is a SQL toolkit and Object-Relational Mapping (ORM) library for Python, which provides a full suite of well-known enterprise-level persistence patterns.",
    "doc_restapi": "A REST API (Representational State Transfer Application Programming Interface) is a set of rules and conventions for building and interacting with web services, allowing different software applications to communicate over the internet.",
    "doc_fastapi": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.",
    "doc_streamlit": "Streamlit is an open-source app framework for Machine Learning and Data Science teams. It allows users to create and share custom web apps for machine learning and data science projects with ease.",
    "doc_pandas": "Pandas is an open-source data analysis and manipulation library for Python. It provides data structures and functions needed to manipulate structured data seamlessly.",
    "doc_numpy": "NumPy is a fundamental package for scientific computing in Python. It provides support for large, multi-dimensional arrays and matrices, along with a collection of mathematical functions to operate on these arrays.",
    "doc_matplotlib": "Matplotlib is a comprehensive library for creating static, animated, and interactive visualizations in Python. It is widely used for plotting and data visualization tasks.",
    "doc_sentence_transformers": "Sentence Transformers is a Python framework for state-of-the-art sentence, text, and image embeddings. It allows users to easily compute dense vector representations for sentences and paragraphs, enabling various natural language processing tasks such as semantic search, clustering, and classification.",
    "doc_openai": "OpenAI is an artificial intelligence research organization that aims to ensure that artificial general intelligence (AGI) benefits all of humanity. It conducts research in various areas of AI, including natural language processing, reinforcement learning, and robotics.",
}

metadatas = [
    {"topic": "ai_hallucination"},
    {"topic": "machine_learning"},
    {"topic": "natural_language_processing"},
    {"topic": "sqlalchemy"},
    {"topic": "restapi"},
    {"topic": "fastapi"},
    {"topic": "streamlit"},
    {"topic": "pandas"},
    {"topic": "numpy"},
    {"topic": "matplotlib"},
    {"topic": "sentence_transformers"},
    {"topic": "openai"},
]

doc_ids = ids
doc_texts = list(documents.values())
if model is None:
    print("Using local TF-IDF fallback. Set USE_SEMANTIC_MODEL=1 after downloading the model.")
    vectorizer = TfidfVectorizer()
    doc_embeddings = vectorizer.fit_transform(doc_texts).toarray()
else:
    vectorizer = None
    doc_embeddings = model.encode(doc_texts)

client = chromadb.EphemeralClient()
collection = client.get_or_create_collection("eval_collection")
collection.upsert(
    ids=doc_ids,
    documents=doc_texts,
    metadatas=metadatas,
    embeddings=doc_embeddings.tolist(),
)

EVAL_SET = [
    {"query": "What is AI hallucination?", "relevant_sources": ["doc_ai_hallucination"]},
    {"query": "What is machine learning?", "relevant_sources": ["doc_machine_learning"]},
    {"query": "What is natural language processing?", "relevant_sources": ["doc_natural_language_processing"]},
    {"query": "What is SQLAlchemy?", "relevant_sources": ["doc_sqlalchemy"]},
    {"query": "What is a REST API?", "relevant_sources": ["doc_restapi"]},
    {"query": "What is FastAPI?", "relevant_sources": ["doc_fastapi"]},
    {"query": "What is Streamlit?", "relevant_sources": ["doc_streamlit"]},
    {"query": "What is Pandas?", "relevant_sources": ["doc_pandas"]},
    {"query": "What is NumPy?", "relevant_sources": ["doc_numpy"]},
    {"query": "What is Matplotlib?", "relevant_sources": ["doc_matplotlib"]},
    {"query": "What is Sentence Transformers?", "relevant_sources": ["doc_sentence_transformers"]},
    {"query": "What is OpenAI?", "relevant_sources": ["doc_openai"]},
]




def precision_recall(
    retrieved_sources: list[str], relevant_sources: list[str]
) -> tuple[float, float]:
    """
    Compute source-level precision and recall.

    Returns (precision, recall) as floats in [0, 1].
    """
    pass

def evaluate(n_results: int = 5, distance_threshold: float = None):
    """
    Run every query in EVAL_SET and print per-query and average precision/recall.
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate search quality")
    parser.add_argument("--n-results", type=int,   default=5)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()
    evaluate(n_results=args.n_results, distance_threshold=args.threshold)
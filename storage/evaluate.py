"""
Evaluates semantic search performance across different chunk sizes (200 vs 500 characters).

Calculates Top 3 distance scores, assigns relevance based on a cosine distance 
threshold, computes Precision@3, and outputs formatted Markdown results.
"""

import sys
from pathlib import Path

# Add project root to sys.path to enable imports across modules
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import chromadb

# Configuration Constants
CHROMA_PATH = ROOT_DIR / "storage" / "chroma_data"
DISTANCE_THRESHOLD = 0.80  # Distances < 0.80 are classified as Relevant (R)

EVALUATION_QUERIES = [
    "How does FastAPI validate data?",
    "What is the difference between FastAPI and Flask?",
    "How do I deploy a FastAPI app?",
    "What are the benefits of using FastAPI?",
    "How can I test a FastAPI application?",
]


def get_chroma_client(db_path: Path) -> chromadb.PersistentClient:
    """Initializes and returns a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=str(db_path))


def evaluate_query_on_collection(
    client: chromadb.PersistentClient,
    collection_name: str,
    query: str,
    n_results: int = 3,
    threshold: float = DISTANCE_THRESHOLD,
) -> dict:
    """Queries a specific ChromaDB collection for top N matches and determines relevance."""
    try:
        collection = client.get_collection(name=collection_name)
        results = collection.query(query_texts=[query], n_results=n_results)
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return {"ranks": [], "precision_at_3": 0.0}

    ranks = []
    relevant_count = 0

    if results and results.get("documents") and len(results["documents"][0]) > 0:
        for i in range(len(results["documents"][0])):
            distance = results["distances"][0][i] if "distances" in results else 1.0
            doc_text = results["documents"][0][i]
            is_relevant = distance < threshold

            if is_relevant:
                relevant_count += 1

            # Format snippet cleanly
            clean_text = doc_text.replace("\n", " ").strip()
            snippet = clean_text[:80] + ("..." if len(clean_text) > 80 else "")

            ranks.append({
                "rank": i + 1,
                "distance": distance,
                "relevant": is_relevant,
                "snippet": snippet,
            })

    # Fixed denominator: Precision@K should divide by requested K (n_results)
    precision_at_k = relevant_count / float(n_results)

    return {
        "ranks": ranks,
        "precision_at_3": precision_at_k,
    }


def run_experiment(queries: list[str]) -> list[dict]:
    """Runs the full chunk-size evaluation experiment across all queries for 200 and 500 character collections."""
    client = get_chroma_client(CHROMA_PATH)
    experiment_results = []

    for query in queries:
        eval_200 = evaluate_query_on_collection(client, "semantic_search_200", query, n_results=3)
        eval_500 = evaluate_query_on_collection(client, "semantic_search_500", query, n_results=3)

        experiment_results.append({
            "query": query,
            "200_char": eval_200,
            "500_char": eval_500,
        })

    return experiment_results


def print_formatted_results(results: list[dict]) -> None:
    """Prints comparative detailed logs and outputs a markdown table for README documentation."""
    print("=" * 80)
    print("CHUNK-SIZE EXPERIMENT EVALUATION RESULTS (Top 3 Scoring)")
    print(f"Relevance Threshold: Cosine Distance < {DISTANCE_THRESHOLD}")
    print("=" * 80 + "\n")

    p3_200_scores = []
    p3_500_scores = []

    # Detailed Console Output
    for item in results:
        print(f"QUERY: '{item['query']}'")
        for chunk_key in ["200_char", "500_char"]:
            data = item[chunk_key]
            if chunk_key == "200_char":
                p3_200_scores.append(data["precision_at_3"])
            else:
                p3_500_scores.append(data["precision_at_3"])

            print(f"  [{chunk_key.upper()}] (Precision@3: {data['precision_at_3']:.2f})")
            for r in data["ranks"]:
                rel_str = "RELEVANT" if r["relevant"] else "IRRELEVANT"
                print(f"    Rank {r['rank']}: Score = {r['distance']:.4f} | [{rel_str}] | Snippet: {r['snippet']}")
        print("-" * 80)

    # Calculate Aggregate Mean Precision@3
    mean_p3_200 = sum(p3_200_scores) / max(1, len(p3_200_scores))
    mean_p3_500 = sum(p3_500_scores) / max(1, len(p3_500_scores))

    print(f"\nAGGREGATE SUMMARY:")
    print(f"  200-char Collection Mean Precision@3: {mean_p3_200:.2f}")
    print(f"  500-char Collection Mean Precision@3: {mean_p3_500:.2f}")

    # Markdown Table Generation for README.md
    print("\n\n### README Markdown Table Output:\n")
    print("| Query | Collection | Rank 1 (Score / Rel) | Rank 2 (Score / Rel) | Rank 3 (Score / Rel) | Precision@3 |")
    print("| :--- | :--- | :--- | :--- | :--- | :---: |")

    for item in results:
        q_text = item["query"]
        for size_label, chunk_key in [("200-char", "200_char"), ("500-char", "500_char")]:
            ranks = item[chunk_key]["ranks"]
            rank_cols = []

            for i in range(3):
                if i < len(ranks):
                    r = ranks[i]
                    status = "R" if r["relevant"] else "I"
                    rank_cols.append(f"{r['distance']:.4f} ({status})")
                else:
                    rank_cols.append("N/A")

            p3 = item[chunk_key]["precision_at_3"]
            first_col = f"**{q_text}**" if size_label == "200-char" else ""
            print(f"| {first_col} | {size_label} | {rank_cols[0]} | {rank_cols[1]} | {rank_cols[2]} | {p3:.2f} |")


if __name__ == "__main__":
    results = run_experiment(EVALUATION_QUERIES)
    print_formatted_results(results)
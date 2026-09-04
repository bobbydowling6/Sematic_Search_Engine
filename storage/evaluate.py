"""Compare the same five queries across the 200- and 500-character indexes."""

import argparse

from search import search


CHUNK_SIZES = (200, 500)
QUERIES = [
    "How does FastAPI validate data?",
    "What is the difference between FastAPI and Flask?",
    "How do I deploy a FastAPI app?",
    "What are the benefits of using FastAPI?",
    "How can I test a FastAPI application?",
]


def evaluate(n_results: int = 1) -> list[dict]:
    comparisons = []
    for query in QUERIES:
        results_by_size = {
            size: search(query, n_results=n_results, collection_name=f"semantic_search_{size}")
            for size in CHUNK_SIZES
        }
        distances = {
            size: results[0]["distance"] if results else None
            for size, results in results_by_size.items()
        }
        available = {size: distance for size, distance in distances.items() if distance is not None}
        winner = min(available, key=available.get) if available else None
        comparisons.append({"query": query, "distances": distances, "winner": winner})
        print(query)
        for size in CHUNK_SIZES:
            distance = distances[size]
            print(f"  {size}: {distance:.4f}" if distance is not None else f"  {size}: no result")
        print(f"  better: {winner or 'no result'}")

    wins = {size: sum(item["winner"] == size for item in comparisons) for size in CHUNK_SIZES}
    overall = max(wins, key=wins.get)
    print(f"Overall: {overall} characters ({wins[overall]}/{len(QUERIES)} query wins)")
    return comparisons


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare chunk-size indexes")
    parser.add_argument("--n-results", type=int, default=1)
    args = parser.parse_args()
    evaluate(n_results=args.n_results)
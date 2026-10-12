"""Compare three retrieval models with standard ranked-retrieval metrics."""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from pathlib import Path

from retrieval_models import create_models, load_documents, parse_cisi_records


def parse_queries(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = list(re.finditer(r"^\.I\s+(\d+)\s*$", text, flags=re.MULTILINE))
    queries: dict[str, str] = {}
    for position, marker in enumerate(markers):
        end = markers[position + 1].start() if position + 1 < len(markers) else len(text)
        block = text[marker.end():end]
        block = re.sub(r"^\.[A-Z]\s*$", " ", block, flags=re.MULTILINE)
        queries[marker.group(1)] = " ".join(block.split())
    return queries


def parse_relevance(path: Path) -> dict[str, set[str]]:
    judgments: dict[str, set[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) >= 2:
            judgments.setdefault(fields[0], set()).add(fields[1])
    return judgments


def calculate_metrics(ranked: list[str], relevant: set[str], k: int) -> dict[str, float]:
    """Calculate cut-off and full-ranking measures for one query."""
    if k < 1:
        raise ValueError("k must be at least 1")
    if not relevant:
        return {"precision": 0.0, "recall": 0.0, "ap": 0.0, "rr": 0.0, "ndcg": 0.0}

    top_k = ranked[:k]
    hits_at_k = sum(doc_id in relevant for doc_id in top_k)
    precision = hits_at_k / k
    recall = hits_at_k / len(relevant)

    relevant_seen = 0
    precision_sum = 0.0
    first_relevant_rank = 0
    dcg = 0.0
    for rank, doc_id in enumerate(ranked, start=1):
        if doc_id in relevant:
            relevant_seen += 1
            precision_sum += relevant_seen / rank
            if first_relevant_rank == 0:
                first_relevant_rank = rank
            if rank <= k:
                dcg += 1.0 / math.log2(rank + 1)

    ideal_hits = min(k, len(relevant))
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return {
        "precision": precision,
        "recall": recall,
        "ap": precision_sum / len(relevant),
        "rr": 1.0 / first_relevant_rank if first_relevant_rank else 0.0,
        "ndcg": dcg / ideal_dcg if ideal_dcg else 0.0,
    }


def evaluate_models(documents, queries, judgments, k: int = 5, timing_runs: int = 200):
    models = create_models(documents)
    results: dict[str, dict] = {}
    for model in models:
        rows = []
        evaluated = [(query_id, query) for query_id, query in queries.items() if query_id in judgments]
        for query_id, query in evaluated:
            ranked = [item.doc_id for item in model.search(query, top_k=len(documents))]
            rows.append({"query_id": query_id, **calculate_metrics(ranked, judgments[query_id], k)})

        start = time.perf_counter()
        for _ in range(timing_runs):
            for _, query in evaluated:
                model.search(query, top_k=k)
        elapsed = time.perf_counter() - start
        mean_latency_ms = elapsed * 1000 / (timing_runs * len(evaluated))

        metrics = ("precision", "recall", "ap", "rr", "ndcg")
        mean = {metric: sum(row[metric] for row in rows) / len(rows) for metric in metrics}
        results[model.name] = {"rows": rows, "mean": mean, "mean_latency_ms": mean_latency_ms}
    return results, models[0].corpus


def load_sample(base: Path):
    documents = load_documents(base / "data/sample_documents.json")
    items = json.loads((base / "data/sample_queries.json").read_text(encoding="utf-8"))
    queries = {item["id"]: item["text"] for item in items}
    judgments = {item["id"]: set(item["relevant"]) for item in items}
    return documents, queries, judgments


def print_results(results: dict, k: int) -> None:
    print(f"{'MODEL':<18} {'P@'+str(k):>7} {'R@'+str(k):>7} {'MAP':>7} {'MRR':>7} {'nDCG@'+str(k):>9} {'ms/query':>10}")
    print("-" * 72)
    for name, result in results.items():
        mean = result["mean"]
        print(
            f"{name:<18} {mean['precision']:7.3f} {mean['recall']:7.3f} "
            f"{mean['ap']:7.3f} {mean['rr']:7.3f} {mean['ndcg']:9.3f} "
            f"{result['mean_latency_ms']:10.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true", help="Use the bundled offline demonstration corpus")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--timing-runs", type=int, default=200)
    parser.add_argument("--json", type=Path, help="Optional output file")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent

    if args.sample:
        documents, queries, judgments = load_sample(base)
        label = "OFFLINE DEMONSTRATION — NOT A FULL CISI BENCHMARK"
    else:
        files = [args.data_dir / filename for filename in ("CISI.ALL", "CISI.QRY", "CISI.REL")]
        if not all(path.exists() for path in files):
            raise SystemExit("Full CISI files not found. Run with --sample or add CISI.ALL/QRY/REL to data/.")
        documents = parse_cisi_records(files[0])
        queries = parse_queries(files[1])
        judgments = parse_relevance(files[2])
        label = "FULL CISI COLLECTION"

    results, corpus = evaluate_models(documents, queries, judgments, args.top_k, args.timing_runs)
    print(label)
    print(f"Documents: {len(documents)} | Queries: {len(queries)} | Vocabulary: {corpus.vocabulary_size} | k={args.top_k}\n")
    print_results(results, args.top_k)
    if args.json:
        payload = {
            "label": label,
            "documents": len(documents),
            "queries": len(queries),
            "vocabulary": corpus.vocabulary_size,
            "k": args.top_k,
            "models": results,
        }
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()


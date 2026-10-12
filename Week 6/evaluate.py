"""Evaluate the IR system against CISI or bundled demonstration judgments."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from ir_system import TfidfIndex, load_sample_documents, parse_cisi_records


def parse_queries(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(re.finditer(r"^\.I\s+(\d+)\s*$", text, flags=re.MULTILINE))
    queries: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():end]
        content = re.sub(r"^\.[A-Z]\s*$", " ", block, flags=re.MULTILINE)
        queries[match.group(1)] = " ".join(content.split())
    return queries


def parse_relevance(path: Path) -> dict[str, set[str]]:
    relevance: dict[str, set[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        columns = line.split()
        if len(columns) >= 2:
            relevance.setdefault(columns[0], set()).add(columns[1])
    return relevance


def ranked_metrics(ranked: list[str], relevant: set[str], k: int) -> dict[str, float]:
    if not relevant:
        return {"precision": 0.0, "recall": 0.0, "ap": 0.0, "rr": 0.0, "ndcg": 0.0}
    top = ranked[:k]
    hits = [1 if doc_id in relevant else 0 for doc_id in top]
    precision = sum(hits) / k
    recall = sum(hits) / len(relevant)

    found = 0
    precision_sum = 0.0
    first_rank = 0
    dcg = 0.0
    for rank, doc_id in enumerate(ranked, start=1):
        if doc_id in relevant:
            found += 1
            precision_sum += found / rank
            if not first_rank:
                first_rank = rank
        if rank <= k and doc_id in relevant:
            dcg += 1.0 / math.log2(rank + 1)
    average_precision = precision_sum / len(relevant)
    ideal_hits = min(k, len(relevant))
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return {
        "precision": precision,
        "recall": recall,
        "ap": average_precision,
        "rr": 1.0 / first_rank if first_rank else 0.0,
        "ndcg": dcg / ideal_dcg if ideal_dcg else 0.0,
    }


def evaluate(index: TfidfIndex, queries: dict[str, str], relevance: dict[str, set[str]], k: int) -> tuple[list[dict], dict[str, float]]:
    rows = []
    for query_id in sorted(queries, key=lambda value: int(value[1:]) if value.startswith("Q") else int(value)):
        if query_id not in relevance:
            continue
        ranked = [result.doc_id for result in index.search(queries[query_id], top_k=len(index.documents))]
        metrics = ranked_metrics(ranked, relevance[query_id], k)
        rows.append({"query_id": query_id, "query": queries[query_id], **metrics})
    if not rows:
        raise ValueError("No evaluated queries matched the relevance judgments")
    mean = {name: sum(row[name] for row in rows) / len(rows) for name in ("precision", "recall", "ap", "rr", "ndcg")}
    return rows, mean


def load_sample(base: Path):
    documents = load_sample_documents(base / "data/sample_documents.json")
    items = json.loads((base / "data/sample_queries.json").read_text(encoding="utf-8"))
    queries = {item["id"]: item["text"] for item in items}
    relevance = {item["id"]: set(item["relevant"]) for item in items}
    return documents, queries, relevance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true", help="Use bundled offline demonstration data")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", type=Path, help="Optional path for machine-readable results")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent

    if args.sample:
        documents, queries, relevance = load_sample(base)
        label = "OFFLINE DEMONSTRATION (not full CISI benchmark)"
    else:
        data_dir = args.data_dir.resolve()
        required = [data_dir / name for name in ("CISI.ALL", "CISI.QRY", "CISI.REL")]
        if not all(path.exists() for path in required):
            raise SystemExit("Full CISI files not found. Run download_data.py or pass --sample.")
        documents = parse_cisi_records(required[0])
        queries = parse_queries(required[1])
        relevance = parse_relevance(required[2])
        label = "FULL CISI COLLECTION"

    index = TfidfIndex(documents)
    rows, mean = evaluate(index, queries, relevance, args.top_k)
    print(label)
    print(f"Documents: {len(documents)} | Queries evaluated: {len(rows)} | Vocabulary: {index.vocabulary_size}")
    print(f"{'ID':<5} {'P@'+str(args.top_k):>7} {'R@'+str(args.top_k):>7} {'AP':>7} {'RR':>7} {'nDCG@'+str(args.top_k):>9}")
    for row in rows:
        print(f"{row['query_id']:<5} {row['precision']:7.3f} {row['recall']:7.3f} {row['ap']:7.3f} {row['rr']:7.3f} {row['ndcg']:9.3f}")
    print("-" * 47)
    print(f"MEAN  {mean['precision']:7.3f} {mean['recall']:7.3f} {mean['ap']:7.3f} {mean['rr']:7.3f} {mean['ndcg']:9.3f}")

    if args.json:
        args.json.write_text(json.dumps({"label": label, "rows": rows, "mean": mean}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()


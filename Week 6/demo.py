"""Run three readable searches over the bundled offline demonstration corpus."""

from pathlib import Path

from ir_system import TfidfIndex, load_sample_documents


BASE = Path(__file__).resolve().parent
QUERIES = [
    "automatic text indexing and document retrieval",
    "university library administration and planning",
    "precision recall ranked retrieval evaluation",
]


def main() -> None:
    documents = load_sample_documents(BASE / "data/sample_documents.json")
    index = TfidfIndex(documents)
    print(f"TF-IDF index ready: {len(documents)} documents, {index.vocabulary_size} terms\n")
    for query in QUERIES:
        print(f"QUERY: {query}")
        for rank, result in enumerate(index.search(query, top_k=3), start=1):
            print(f"  {rank}. {result.doc_id}  {result.score:.4f}  {result.title}")
        print()


if __name__ == "__main__":
    main()


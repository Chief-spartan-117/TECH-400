"""Display the top three results from every model for one query."""

from pathlib import Path

from evaluate_models import load_sample
from retrieval_models import create_models


BASE = Path(__file__).resolve().parent
QUERY = "library acquisition and machine readable bibliographic records"


def main() -> None:
    documents, _, _ = load_sample(BASE)
    print(f"Query: {QUERY}\n")
    for model in create_models(documents):
        print(model.name)
        for rank, result in enumerate(model.search(QUERY, top_k=3), start=1):
            print(f"  {rank}. {result.doc_id}  {result.score:.4f}  {result.title}")
        print()


if __name__ == "__main__":
    main()


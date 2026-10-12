"""Download and validate the public CISI document, query, and judgment files."""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from evaluate_models import parse_queries, parse_relevance
from retrieval_models import parse_cisi_records


BASE_URL = "https://raw.githubusercontent.com/GianRomani/CISI-project-MLOps/master"
FILENAMES = ("CISI.ALL", "CISI.QRY", "CISI.REL")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    for filename in FILENAMES:
        destination = args.output / filename
        request = urllib.request.Request(
            f"{BASE_URL}/{filename}", headers={"User-Agent": "week-7-ir-evaluation/1.0"}
        )
        print(f"Downloading {filename} ...")
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())

    documents = parse_cisi_records(args.output / "CISI.ALL")
    queries = parse_queries(args.output / "CISI.QRY")
    judgments = parse_relevance(args.output / "CISI.REL")
    if len(documents) != 1460:
        raise ValueError(f"Expected 1,460 documents; parsed {len(documents)}")
    if len(queries) != 112:
        raise ValueError(f"Expected 112 queries; parsed {len(queries)}")
    if not judgments:
        raise ValueError("No relevance judgments were parsed")
    print(
        f"Validated {len(documents)} documents, {len(queries)} queries, "
        f"and {sum(map(len, judgments.values()))} judgments."
    )


if __name__ == "__main__":
    main()


"""Download the three public CISI collection files and validate their structure."""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from evaluate import parse_queries, parse_relevance
from ir_system import parse_cisi_records


BASE_URL = "https://raw.githubusercontent.com/GianRomani/CISI-project-MLOps/master"
FILES = ("CISI.ALL", "CISI.QRY", "CISI.REL")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    for name in FILES:
        destination = args.output / name
        print(f"Downloading {name} ...")
        request = urllib.request.Request(f"{BASE_URL}/{name}", headers={"User-Agent": "week-6-ir-assignment/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())

    documents = parse_cisi_records(args.output / "CISI.ALL")
    queries = parse_queries(args.output / "CISI.QRY")
    relevance = parse_relevance(args.output / "CISI.REL")
    if len(documents) != 1460:
        raise ValueError(f"Expected 1,460 documents; parsed {len(documents)}")
    if len(queries) != 112:
        raise ValueError(f"Expected 112 queries; parsed {len(queries)}")
    if not relevance:
        raise ValueError("No relevance judgments were parsed")
    print(f"Validated: {len(documents)} documents, {len(queries)} queries, {sum(map(len, relevance.values()))} judgments")


if __name__ == "__main__":
    main()


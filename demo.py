"""
demo.py
-------
Builds the IR system from the sample 8-document collection in docs/,
prints the dictionary and inverted index, then runs a set of sample
Boolean queries and prints the results.

Run with:  python3 demo.py
"""

import os
from ir_system import IRSystem

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "docs")

SAMPLE_QUERIES = [
    "python",
    "language",
    "python OR java",
    "language AND retrieval",
    "programming AND NOT java",
    "boolean AND retrieval",
    "(python OR java) AND language",
    "machine AND learning",
]


def main():
    ir = IRSystem()
    ir.add_documents_from_folder(DOCS_FOLDER)

    print("=" * 60)
    print("DOCUMENT COLLECTION")
    print("=" * 60)
    for doc_id in sorted(ir.documents):
        name = ir.doc_names[doc_id]
        preview = ir.documents[doc_id].strip().replace("\n", " ")
        if len(preview) > 70:
            preview = preview[:70] + "..."
        print(f"  [{doc_id}] {name:<10} {preview}")

    print()
    print("=" * 60)
    print(f"DICTIONARY  ({len(ir.get_dictionary())} distinct terms)")
    print("=" * 60)
    print(", ".join(ir.get_dictionary()))

    print()
    print("=" * 60)
    print("INVERTED INDEX")
    print("=" * 60)
    ir.print_index()

    print()
    print("=" * 60)
    print("BOOLEAN QUERIES")
    print("=" * 60)
    for q in SAMPLE_QUERIES:
        result = sorted(ir.search(q))
        names = [ir.doc_names[d] for d in result]
        print(f"  Query: {q!r:<32} -> docs {result}  {names}")


if __name__ == "__main__":
    main()

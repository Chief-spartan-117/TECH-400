# Week 6 — Basic Information Retrieval System

This project implements a small, explainable information retrieval (IR) system for the
public CISI collection. It uses an inverted index and ltc-style TF–IDF cosine similarity,
with the same preprocessing applied to documents and queries.

The repository includes a compact offline demonstration corpus so every command works
without network access. `download_data.py` retrieves the full CISI files when an internet
connection is available. Scores produced from the demonstration corpus are illustrative;
they must not be presented as full CISI benchmark results.

## Project contents

```text
Week 6/
├── data/                      Offline demonstration data; full CISI files go here
├── screenshots/               Report figures generated from actual code/output
├── tests/                     Unit tests
├── demo.py                    Run example searches
├── download_data.py           Download and validate CISI.ALL/QRY/REL
├── evaluate.py                P@k, Recall@k, MAP, MRR, and nDCG@k
├── ir_system.py               Parser, preprocessing, index, and retrieval
├── make_report.py             Build the DOCX report
├── make_screenshots.py        Rebuild report snapshots
└── report.docx                Submission-ready report (identity/link placeholders remain)
```

## Quick start (offline)

Python 3.10+ is recommended. The retrieval code uses only the standard library.

```bash
python3 demo.py
python3 evaluate.py --sample
python3 -m unittest discover -s tests -v
```

## Run with the full CISI collection

```bash
python3 download_data.py
python3 evaluate.py --data-dir data --top-k 10
python3 ir_system.py --corpus data/CISI.ALL --query "automatic text indexing" --top-k 5
```

## Retrieval pipeline

1. Parse the `.I`, `.T`, `.A`, and `.W` fields in the CISI records.
2. Normalize Unicode and lowercase the text.
3. Tokenize alphabetic terms, remove stop words, and apply conservative suffix stemming.
4. Build an inverted index containing document term frequencies.
5. Weight terms with `1 + log(tf)` and smoothed IDF.
6. Normalize document and query vectors and rank by cosine similarity.
7. Evaluate ranked lists using the supplied relevance judgments.

## GitHub submission

Authenticate, create the remote repository, then push the prepared `main` branch:

```bash
gh auth login
gh repo create YOUR_USERNAME/week-6-ir-system --public
git push -u origin main
```

Replace `YOUR_USERNAME` in this README and in `make_report.py`, rerun
`python3 make_report.py`, and submit the resulting GitHub URL with `report.docx`.

## Dataset source

- Original CISI collection: University of Glasgow IR test collections archive
- Reproducible mirror used by the downloader:
  <https://github.com/GianRomani/CISI-project-MLOps>


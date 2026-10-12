# Week 7 — Evaluation of Information Retrieval Models

This project continues the Week 6 CISI information-retrieval system and compares
three retrieval models under the same preprocessing, documents, queries, and
relevance judgments:

1. Binary term-overlap baseline
2. TF–IDF cosine similarity
3. Okapi BM25 (`k1=1.5`, `b=0.75`)

The evaluation calculates Precision@k, Recall@k, Average Precision/MAP,
Reciprocal Rank/MRR, nDCG@k, and descriptive mean query latency.

## Run the included offline experiment

```bash
python3 evaluate_models.py --sample --top-k 5 --json results.json
python3 demo.py
python3 -m unittest discover -s tests -v
```

The bundled 18-document/eight-query corpus makes the project runnable without
internet access. Its scores are demonstration results, not full CISI benchmark
results.

## Run the full CISI evaluation

```bash
python3 download_data.py
python3 evaluate_models.py --data-dir data --top-k 10 --json full_cisi_results.json
```

The downloader validates the expected 1,460 documents and 112 queries before
the experiment runs.

## Rebuild report artifacts

```bash
python3 make_screenshots.py
python3 make_report.py
```

`report.docx` contains the method, commented implementation extracts, actual
output snapshots, per-model results, metric definitions, and limitations.

## GitHub publication

The repository is prepared for:

<https://github.com/Chief-spartan-117/week-7-ir-evaluation>

Authenticate and publish it with:

```bash
gh auth login
gh repo create Chief-spartan-117/week-7-ir-evaluation --public
git push -u origin main
```

## Sources

- CISI collection: <https://ir.dcs.gla.ac.uk/resources/test_collections/cisi/>
- Evaluation concepts: <https://nlp.stanford.edu/IR-book/>


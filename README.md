# doc-similarity-vsm

Document similarity scoring using a Vector Space Model (TF-IDF + cosine
similarity), implemented from scratch in Python.

- 8 public documents (Wikipedia extracts) in `docs/`, one per topic.
- `vsm.py` — tokenizer, TF-IDF weighting, cosine similarity, from-scratch (numpy for vector math only).
- Full write-up, code walkthrough, and result screenshots: [`REPORT.md`](REPORT.md).

## Quick start

```bash
pip install -r requirements.txt
python3 vsm.py
```

## Result preview

![Similarity heatmap](screenshots/04_similarity_heatmap.png)

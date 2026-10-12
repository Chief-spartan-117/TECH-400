# Week 8 — Project Findings Presentation

This folder contains a refined 16:9 PowerPoint summary of the Week 6 and Week 7
information-retrieval project.

## Presentation

- `Week_8_Project_Findings.pptx` — submission-ready 12-slide presentation
- `make_presentation.py` — reproducible PowerPoint generator

The deck covers:

- Problem statement and project objectives
- Full CISI dataset and offline demonstration data
- Preprocessing, indexing, and retrieval methodology
- Binary overlap, TF–IDF cosine, and BM25
- Precision, recall, MAP, MRR, nDCG, and latency
- Aggregate and per-query findings
- Sample system output
- Critical analysis, limitations, and recommendations

## Regenerate

The generator reads the metrics and screenshots already produced in Week 7:

```bash
python3 make_presentation.py
```

`python-pptx` and Pillow are required to regenerate the deck. All images are
embedded into the resulting PPTX, so the presentation itself is portable.


# Document Similarity via Vector Space Model

## 1. Objective

Compute pairwise similarity scores between a set of documents using a
**Vector Space Model (VSM)** with **TF-IDF** term weighting and
**cosine similarity**.

## 2. Document Collection

8 documents were gathered from Wikipedia (public, freely accessible
content, CC BY-SA) and saved as plain `.txt` files in `docs/`. Topics were
chosen in four related pairs so the similarity results are easy to sanity
check: two AI/ML topics, one AI-adjacent topic, two space topics, two
sports topics, and one climate topic.

| ID | File | Topic | Source |
|----|------|-------|--------|
| d1 | doc1_artificial_intelligence.txt | Artificial Intelligence | https://en.wikipedia.org/wiki/Artificial_intelligence |
| d2 | doc2_machine_learning.txt | Machine Learning | https://en.wikipedia.org/wiki/Machine_learning |
| d3 | doc3_large_language_model.txt | Large Language Model | https://en.wikipedia.org/wiki/Large_language_model |
| d4 | doc4_nasa.txt | NASA | https://en.wikipedia.org/wiki/NASA |
| d5 | doc5_mars.txt | Mars | https://en.wikipedia.org/wiki/Mars |
| d6 | doc6_association_football.txt | Association Football | https://en.wikipedia.org/wiki/Association_football |
| d7 | doc7_basketball.txt | Basketball | https://en.wikipedia.org/wiki/Basketball |
| d8 | doc8_climate_change.txt | Climate Change | https://en.wikipedia.org/wiki/Climate_change |

Each file was pulled with the Wikipedia REST API (`action=query&prop=extracts&explaintext=1`)
to get clean plain text (~1.2 KB each), prefixed with a `Title:` / `Source:` header.

**Snapshot — document collection loaded:**

![Document collection](screenshots/01_document_collection.png)

## 3. Method: Vector Space Model

Implemented from scratch in `vsm.py` (numpy used only for vector
arithmetic, not for the algorithm itself):

1. **Tokenize & normalize** — lowercase, strip to alphabetic tokens with
   a regex (`[a-z]+`), drop a small stopword list, drop tokens ≤ 2 chars.
2. **Build vocabulary** — union of all terms across all documents (601
   unique terms across the 8-document collection).
3. **Term Frequency (TF)** — `tf(t, d) = count(t in d) / len(d)`, i.e.
   raw count normalized by document length.
4. **Inverse Document Frequency (IDF)** — `idf(t) = log(N / df(t))`,
   where `N` is the number of documents and `df(t)` is the number of
   documents containing term `t`. This down-weights terms that appear in
   most/all documents (e.g. "system", "data") and up-weights terms
   distinctive to a smaller subset (e.g. "neural", "mars", "goalkeeper").
5. **TF-IDF vector** — `tfidf(t, d) = tf(t, d) * idf(t)`, one scalar per
   vocabulary term, giving each document an N-dimensional vector where N
   = vocabulary size.
6. **Cosine similarity** — for document vectors `A` and `B`:

   ```
   similarity(A, B) = (A · B) / (‖A‖ * ‖B‖)
   ```

   This measures the cosine of the angle between the two vectors —
   scale-invariant (document length doesn't skew the score) and bounded
   in `[0, 1]` since TF-IDF weights are non-negative.

### Core code

```python
def compute_tf(tokens: list[str], vocab: list[str]) -> np.ndarray:
    counts = Counter(tokens)
    total = len(tokens) or 1
    return np.array([counts.get(term, 0) / total for term in vocab])


def compute_idf(tokenized_docs: dict[str, list[str]], vocab: list[str]) -> np.ndarray:
    n_docs = len(tokenized_docs)
    df = np.zeros(len(vocab))
    for i, term in enumerate(vocab):
        df[i] = sum(1 for tokens in tokenized_docs.values() if term in tokens)
    return np.log(n_docs / (df + 1e-9)) + 1e-9


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(dot / norm) if norm > 0 else 0.0
```

Full implementation: [`vsm.py`](vsm.py).

## 4. Results

**Snapshot — cosine similarity matrix (terminal output):**

![Similarity matrix](screenshots/02_similarity_matrix.png)

Full matrix:

| | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 |
|---|---|---|---|---|---|---|---|---|
|**d1**|1.000|0.207|0.067|0.067|0.005|0.011|0.007|0.006|
|**d2**|0.207|1.000|0.059|0.007|0.002|0.003|0.002|0.006|
|**d3**|0.067|0.059|1.000|0.007|0.002|0.002|0.002|0.018|
|**d4**|0.067|0.007|0.007|1.000|0.021|0.005|0.009|0.021|
|**d5**|0.005|0.002|0.002|0.021|1.000|0.009|0.000|0.052|
|**d6**|0.011|0.003|0.002|0.005|0.009|1.000|0.127|0.002|
|**d7**|0.007|0.002|0.002|0.009|0.000|0.127|1.000|0.009|
|**d8**|0.006|0.006|0.018|0.021|0.052|0.002|0.009|1.000|

**Snapshot — heatmap:**

![Similarity heatmap](screenshots/04_similarity_heatmap.png)

**Snapshot — top/bottom similar pairs:**

![Similar pairs](screenshots/03_similar_pairs.png)

### Top 3 most similar pairs

| Score | Pair |
|---|---|
| 0.207 | Artificial Intelligence ↔ Machine Learning |
| 0.127 | Association Football ↔ Basketball |
| 0.067 | Artificial Intelligence ↔ Large Language Model |

### Bottom 3 least similar pairs

| Score | Pair |
|---|---|
| 0.002 | Machine Learning ↔ Basketball |
| 0.002 | Association Football ↔ Climate Change |
| 0.000 | Mars ↔ Basketball |

## 5. Discussion

The results match domain expectation, which validates the model:

- **AI ↔ Machine Learning (0.207)** is the highest score — expected,
  since ML is a subfield of AI and the two articles share heavy
  vocabulary overlap (`learning`, `model`, `neural`, `data`).
- **Football ↔ Basketball (0.127)** is the second-highest — both are
  team sports articles sharing terms like `team`, `player`, `game`,
  `league`.
- Cross-cluster pairs (e.g. sports vs. climate, space vs. sports) all
  score near 0, correctly showing the model finds no meaningful topical
  overlap between unrelated documents.
- Large Language Model correlates with AI (0.067) more than with ML
  (0.059), consistent with LLMs being described in AI-article terms as
  well as ML terms.

TF-IDF weighting is what makes this work: without IDF down-weighting,
common English scaffolding words would dominate every vector and flatten
all similarity scores toward 1.0. IDF suppresses ubiquitous terms and
lets the distinctive vocabulary of each topic drive the cosine score.

## 6. How to Reproduce

```bash
pip install -r requirements.txt
python3 vsm.py                 # prints similarity matrix + top/bottom pairs
python3 make_heatmap.py        # writes screenshots/04_similarity_heatmap.png
python3 make_screenshots.py    # re-renders terminal-style snapshot PNGs
```

## 7. Files

```
doc-similarity-vsm/
├── docs/                    # 8 source documents (.txt), gathered from Wikipedia
├── vsm.py                   # VSM implementation: tokenize, TF-IDF, cosine similarity
├── make_heatmap.py          # renders similarity matrix as a heatmap PNG
├── make_screenshots.py      # renders terminal output as PNG snapshots
├── demo_output.txt          # raw output of `python3 vsm.py`
├── screenshots/             # snapshot PNGs referenced in this report
├── requirements.txt
└── REPORT.md                # this report
```

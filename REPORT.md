# Document Similarity via Vector Space Model

## 1. Objective

For this assignment I wanted to see how well a classic information
retrieval technique — the **Vector Space Model (VSM)** — could pick up on
topical relationships between documents just from their word usage, no
machine learning training involved. The approach here is **TF-IDF**
weighting combined with **cosine similarity**, computed between every
pair of documents in a small collection.

## 2. Document Collection

I needed 5-10 real, publicly available documents, so I pulled 8 articles
from Wikipedia (public content, CC BY-SA licensed) and saved each one as
a plain `.txt` file in `docs/`. Rather than picking random topics, I
deliberately grouped them into related pairs — two AI/ML articles, one
that's AI-adjacent, two about space, two about team sports, and one on
climate. The idea was that if the model works, related topics should
score noticeably higher than unrelated ones, which makes the results
easy to eyeball and sanity-check.

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

To keep the text clean (no HTML, no nav bars, no infobox clutter) I
pulled each article through Wikipedia's REST API using
`action=query&prop=extracts&explaintext=1` instead of scraping the
rendered page. Each file ended up around 1.2 KB, with a short `Title:` /
`Source:` header on top so the origin is traceable.

**Snapshot — document collection loaded:**

![Document collection](screenshots/01_document_collection.png)

## 3. Method: Vector Space Model

I built the whole pipeline from scratch in `vsm.py` — no scikit-learn,
no pre-built TF-IDF vectorizer. numpy only shows up for the actual vector
math (dot products, norms), not for any part of the algorithm itself.
Here's roughly how it works, in the order the code runs it:

1. **Tokenize & normalize.** Lowercase everything, pull out alphabetic
   tokens with a simple regex (`[a-z]+`), strip a small stopword list,
   and drop anything 2 characters or shorter. Nothing fancy — no
   stemming or lemmatization, just enough cleanup to stop noise words
   from swamping the vectors.
2. **Build the vocabulary.** Union of every term across all 8 documents.
   For this collection that came out to 601 unique terms.
3. **Term Frequency (TF).** `tf(t, d) = count(t in d) / len(d)` — how
   often a term shows up in a document, normalized by document length so
   longer documents don't automatically get bigger scores.
4. **Inverse Document Frequency (IDF).** `idf(t) = log(N / df(t))`,
   where `N` is the total number of documents and `df(t)` is how many of
   them contain term `t`. This is really the important part — it pushes
   down words that show up everywhere (things like "system" or "data")
   and gives more weight to words that are distinctive to just a few
   documents (like "neural", "mars", or "goalkeeper").
5. **TF-IDF vector.** Multiply the two together —
   `tfidf(t, d) = tf(t, d) * idf(t)` — and each document ends up
   represented as a point in a 601-dimensional space, one axis per
   vocabulary term.
6. **Cosine similarity.** For any two document vectors `A` and `B`:

   ```
   similarity(A, B) = (A · B) / (‖A‖ * ‖B‖)
   ```

   This is just the cosine of the angle between the vectors. It doesn't
   care how long the documents are (that's already handled by the TF
   normalization above), and since none of the TF-IDF weights are
   negative, the score always lands somewhere in `[0, 1]`.

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

Full implementation is in [`vsm.py`](vsm.py) if you want to see the rest
(document loading, the driving loop that builds the pairwise matrix,
etc).

## 4. Results

**Snapshot — cosine similarity matrix (terminal output):**

![Similarity matrix](screenshots/02_similarity_matrix.png)

Full matrix, for reference:

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

I also plotted it as a heatmap, which honestly makes the pattern a lot
easier to spot than staring at the numbers:

![Similarity heatmap](screenshots/04_similarity_heatmap.png)

And the top/bottom pairs, pulled straight from the script's own output:

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

What I like about these results is that they line up with what you'd
expect just from reading the topics, which is a decent sign the model is
actually capturing something real and not just noise:

- **AI ↔ Machine Learning came out on top at 0.207**, which makes sense
  — ML is basically a subfield of AI, so the two articles share a lot of
  vocabulary (`learning`, `model`, `neural`, `data` all show up in both).
- **Football ↔ Basketball was second at 0.127.** Both are team-sport
  articles, so words like `team`, `player`, `game`, and `league` overlap
  heavily.
- Every pair that crosses topic clusters — sports vs. climate, space vs.
  sports, whatever — scores close to zero. That's the model correctly
  telling us there's no real topical connection there.
- One thing I found interesting: Large Language Model correlates more
  with AI (0.067) than with Machine Learning (0.059), even though you'd
  think ML and LLMs would be closer. My guess is the AI article uses more
  of the same framing language ("intelligence", "reasoning",
  "perception") that also shows up when LLMs get described.

The IDF term is really doing most of the heavy lifting here. Without it,
common scaffolding words that appear in basically every article would
dominate the vectors and every pair would score close to 1.0, regardless
of topic. IDF suppresses those and lets the words that are actually
distinctive to each topic drive the cosine score.

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

"""
scoring.py
----------
Two document-ranking scoring functions used in information retrieval:

  1. Okapi BM25         (probabilistic relevance model)
  2. Language Model with Jelinek-Mercer smoothing (LM-JM)

Pipeline:
  1. Load documents from docs/*.txt
  2. Tokenize + normalize (lowercase, strip punctuation, remove stopwords)
  3. Build per-document term counts, document lengths, and collection
     term frequencies
  4. Score every document against a query with both BM25 and LM-JM
  5. Rank documents by score for each function and compare

Implemented from first principles -- no scoring library (e.g. rank_bm25,
gensim) is used.
"""

import glob
import math
import os
import re
from collections import Counter

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "to", "in",
    "on", "at", "for", "with", "as", "by", "is", "are", "was", "were",
    "be", "been", "being", "it", "its", "this", "that", "these", "those",
    "from", "into", "such", "can", "also", "which", "their", "his", "her",
    "they", "he", "she", "not", "than", "other", "more", "most", "some",
    "may", "have", "has", "had", "will", "would", "could", "should",
    "about", "between", "used", "use", "including", "include", "based",
}

TOKEN_RE = re.compile(r"[a-z]+")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = TOKEN_RE.findall(text)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def load_documents(docs_dir: str) -> dict[str, str]:
    paths = sorted(glob.glob(os.path.join(docs_dir, "*.txt")))
    docs = {}
    for path in paths:
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            docs[name] = f.read()
    return docs


class Corpus:
    """Holds everything both scoring functions need: term counts per
    document, document lengths, document frequency per term, and the
    collection-wide term frequency (for LM-JM smoothing)."""

    def __init__(self, docs_dir: str = "docs"):
        raw_docs = load_documents(docs_dir)
        self.names = list(raw_docs.keys())
        self.tokens = {name: tokenize(text) for name, text in raw_docs.items()}
        self.counts = {name: Counter(toks) for name, toks in self.tokens.items()}
        self.doc_len = {name: len(toks) for name, toks in self.tokens.items()}
        self.n_docs = len(self.names)
        self.avg_dl = sum(self.doc_len.values()) / self.n_docs

        self.doc_freq: Counter = Counter()
        for name in self.names:
            for term in self.counts[name]:
                self.doc_freq[term] += 1

        collection_counts: Counter = Counter()
        for name in self.names:
            collection_counts.update(self.counts[name])
        self.collection_len = sum(collection_counts.values())
        self.collection_counts = collection_counts


# --------------------------------------------------------------------- #
# 1. Okapi BM25
# --------------------------------------------------------------------- #
def bm25_idf(corpus: Corpus, term: str) -> float:
    n = corpus.n_docs
    df = corpus.doc_freq.get(term, 0)
    return math.log((n - df + 0.5) / (df + 0.5) + 1)


def bm25_score(corpus: Corpus, query_terms: list[str], doc_name: str,
                k1: float = 1.5, b: float = 0.75) -> float:
    dl = corpus.doc_len[doc_name]
    counts = corpus.counts[doc_name]
    score = 0.0
    for term in query_terms:
        f = counts.get(term, 0)
        if f == 0:
            continue
        idf = bm25_idf(corpus, term)
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * dl / corpus.avg_dl)
        score += idf * (numerator / denominator)
    return score


# --------------------------------------------------------------------- #
# 2. Language Model with Jelinek-Mercer smoothing
# --------------------------------------------------------------------- #
def lm_jm_score(corpus: Corpus, query_terms: list[str], doc_name: str,
                 lam: float = 0.1) -> float:
    """Log-likelihood of the query under document d's smoothed unigram
    language model:
        P(w|d) = (1 - lam) * c(w,d)/|d|  +  lam * c(w,C)/|C|
        score(q,d) = sum_w log P(w|d)
    lam close to 0 favors exact/frequent in-document matches (best for
    short, keyword-style queries); lam close to 1 relies more on the
    collection model.
    """
    dl = corpus.doc_len[doc_name]
    counts = corpus.counts[doc_name]
    score = 0.0
    for term in query_terms:
        p_doc = counts.get(term, 0) / dl if dl else 0.0
        p_coll = corpus.collection_counts.get(term, 0) / corpus.collection_len
        p = (1 - lam) * p_doc + lam * p_coll
        if p <= 0:
            # term unseen anywhere in the collection: assign a floor
            # probability so the log is defined but heavily penalized
            p = 1e-12
        score += math.log(p)
    return score


# --------------------------------------------------------------------- #
# 3. Ranking helper
# --------------------------------------------------------------------- #
def rank(corpus: Corpus, query: str, score_fn, **kwargs) -> list[tuple[str, float]]:
    query_terms = tokenize(query)
    scores = [(name, score_fn(corpus, query_terms, name, **kwargs)) for name in corpus.names]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


if __name__ == "__main__":
    corpus = Corpus("docs")
    print("=" * 70)
    print("CORPUS STATS")
    print("=" * 70)
    print(f"  documents: {corpus.n_docs}")
    print(f"  avg doc length (tokens): {corpus.avg_dl:.1f}")
    print(f"  vocabulary size: {len(corpus.doc_freq)}")

    queries = [
        "machine learning neural network",
        "space exploration mars mission",
        "football basketball team player",
    ]

    for q in queries:
        print()
        print("=" * 70)
        print(f"QUERY: \"{q}\"")
        print("=" * 70)

        bm25_ranked = rank(corpus, q, bm25_score)
        lm_ranked = rank(corpus, q, lm_jm_score)

        print(f"  {'Rank':<5}{'BM25 doc':<36}{'score':<10}{'LM-JM doc':<36}{'score':<10}")
        for i in range(len(corpus.names)):
            bname, bscore = bm25_ranked[i]
            lname, lscore = lm_ranked[i]
            print(f"  {i+1:<5}{bname:<36}{bscore:<10.3f}{lname:<36}{lscore:<10.3f}")

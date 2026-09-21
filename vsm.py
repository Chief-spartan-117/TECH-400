"""
vsm.py
------
Vector Space Model (VSM) document similarity.

Pipeline:
  1. Load documents from docs/*.txt
  2. Tokenize + normalize (lowercase, strip punctuation, remove stopwords)
  3. Build vocabulary and term-frequency vectors per document
  4. Weight terms with TF-IDF: tf(t,d) * log(N / df(t))
  5. Represent each document as a TF-IDF vector
  6. Compute pairwise cosine similarity between all document vectors
  7. Report the similarity matrix and the most/least similar document pairs

No ML libraries used for the core algorithm (implemented from first
principles) — numpy is used only for the final vector arithmetic.
"""

import glob
import math
import os
import re
from collections import Counter

import numpy as np

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


def build_vocabulary(tokenized_docs: dict[str, list[str]]) -> list[str]:
    vocab = set()
    for tokens in tokenized_docs.values():
        vocab.update(tokens)
    return sorted(vocab)


def compute_tf(tokens: list[str], vocab: list[str]) -> np.ndarray:
    counts = Counter(tokens)
    total = len(tokens) or 1
    return np.array([counts.get(term, 0) / total for term in vocab])


def compute_idf(tokenized_docs: dict[str, list[str]], vocab: list[str]) -> np.ndarray:
    n_docs = len(tokenized_docs)
    df = np.zeros(len(vocab))
    for i, term in enumerate(vocab):
        df[i] = sum(1 for tokens in tokenized_docs.values() if term in tokens)
    # +1 smoothing avoids division by zero / log(0)
    return np.log(n_docs / (df + 1e-9)) + 1e-9


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(dot / norm) if norm > 0 else 0.0


def build_similarity_matrix(docs_dir: str = "docs"):
    docs = load_documents(docs_dir)
    names = list(docs.keys())
    tokenized = {name: tokenize(text) for name, text in docs.items()}
    vocab = build_vocabulary(tokenized)
    idf = compute_idf(tokenized, vocab)

    tfidf_vectors = {}
    for name in names:
        tf = compute_tf(tokenized[name], vocab)
        tfidf_vectors[name] = tf * idf

    n = len(names)
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            sim_matrix[i, j] = cosine_similarity(tfidf_vectors[names[i]], tfidf_vectors[names[j]])

    return names, vocab, tfidf_vectors, sim_matrix


def print_report(names, vocab, sim_matrix):
    print("=" * 70)
    print("DOCUMENT COLLECTION")
    print("=" * 70)
    for i, name in enumerate(names):
        print(f"  d{i+1}: {name}")

    print()
    print("=" * 70)
    print(f"VOCABULARY SIZE: {len(vocab)} unique terms")
    print("=" * 70)
    print("  sample terms:", ", ".join(vocab[:15]))

    print()
    print("=" * 70)
    print("COSINE SIMILARITY MATRIX (TF-IDF vectors)")
    print("=" * 70)
    header = "        " + "".join(f"d{i+1:<7}" for i in range(len(names)))
    print(header)
    for i, row in enumerate(sim_matrix):
        row_str = "".join(f"{v:<8.3f}" for v in row)
        print(f"  d{i+1:<4}  {row_str}")

    print()
    print("=" * 70)
    print("MOST SIMILAR / LEAST SIMILAR PAIRS")
    print("=" * 70)
    n = len(names)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((sim_matrix[i, j], names[i], names[j]))
    pairs.sort(reverse=True)

    print("  Top 3 most similar pairs:")
    for score, a, b in pairs[:3]:
        print(f"    {score:.3f}  {a}  <->  {b}")

    print("  Bottom 3 least similar pairs:")
    for score, a, b in pairs[-3:]:
        print(f"    {score:.3f}  {a}  <->  {b}")


if __name__ == "__main__":
    names, vocab, tfidf_vectors, sim_matrix = build_similarity_matrix("docs")
    print_report(names, vocab, sim_matrix)

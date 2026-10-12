"""A dependency-free TF-IDF information retrieval system for the CISI collection."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


STOP_WORDS = {
    "a", "about", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being",
    "between", "both", "but", "by", "can", "could", "did", "do", "does",
    "doing", "during", "each", "few", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would", "you", "your", "yours", "yourself",
}


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    author: str = ""
    abstract: str = ""

    @property
    def searchable_text(self) -> str:
        # Repeating the concise title gives it a modest, explainable field boost.
        return f"{self.title} {self.title} {self.author} {self.abstract}"


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    title: str
    score: float


def stem(token: str) -> str:
    """Apply conservative rule-based suffix stripping without external packages."""
    if len(token) > 5 and token.endswith("ies"):
        token = token[:-3] + "y"
    elif len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    for suffix in ("ization", "ational", "fulness", "iveness", "ment", "tion", "ity"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            token = token[: -len(suffix)]
            break
    return token


def preprocess(text: str) -> list[str]:
    """Normalize, tokenize, remove stop words, and stem English text."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    tokens = re.findall(r"[a-z][a-z0-9-]*", normalized.lower())
    return [stem(token) for token in tokens if token not in STOP_WORDS and len(token) > 1]


def parse_cisi_records(path: Path) -> list[Document]:
    """Parse CISI.ALL records while ignoring the cross-reference (.X) field."""
    documents: list[Document] = []
    current_id = ""
    fields: dict[str, list[str]] = defaultdict(list)
    active_field = ""

    def finish() -> None:
        if not current_id:
            return
        documents.append(Document(
            doc_id=current_id,
            title=" ".join(fields["T"]).strip() or f"Document {current_id}",
            author=" ".join(fields["A"]).strip(),
            abstract=" ".join(fields["W"]).strip(),
        ))

    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            match = re.match(r"^\.I\s+(\d+)", line)
            if match:
                finish()
                current_id = match.group(1)
                fields = defaultdict(list)
                active_field = ""
            elif re.match(r"^\.[TAWBX]$", line):
                active_field = line[1]
            elif active_field in {"T", "A", "W"} and line.strip():
                fields[active_field].append(line.strip())
    finish()
    return documents


def load_sample_documents(path: Path) -> list[Document]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Document(item["id"], item["title"], item.get("author", ""), item.get("abstract", "")) for item in data]


class TfidfIndex:
    """In-memory inverted index with logarithmic TF and smoothed IDF weighting."""

    def __init__(self, documents: Iterable[Document]):
        self.documents = {document.doc_id: document for document in documents}
        if not self.documents:
            raise ValueError("At least one document is required")
        self.postings: dict[str, dict[str, int]] = defaultdict(dict)
        self.document_frequency: Counter[str] = Counter()
        self.document_norms: dict[str, float] = {}
        self._build()

    def _idf(self, term: str) -> float:
        n = len(self.documents)
        return math.log((n + 1) / (self.document_frequency.get(term, 0) + 1)) + 1.0

    def _build(self) -> None:
        term_counts: dict[str, Counter[str]] = {}
        for doc_id, document in self.documents.items():
            counts = Counter(preprocess(document.searchable_text))
            term_counts[doc_id] = counts
            for term, frequency in counts.items():
                self.postings[term][doc_id] = frequency
                self.document_frequency[term] += 1

        for doc_id, counts in term_counts.items():
            squared_length = sum(
                ((1.0 + math.log(tf)) * self._idf(term)) ** 2
                for term, tf in counts.items()
            )
            self.document_norms[doc_id] = math.sqrt(squared_length) or 1.0

    @property
    def vocabulary_size(self) -> int:
        return len(self.postings)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_counts = Counter(preprocess(query))
        query_weights = {
            term: (1.0 + math.log(tf)) * self._idf(term)
            for term, tf in query_counts.items()
            if term in self.postings
        }
        query_norm = math.sqrt(sum(weight * weight for weight in query_weights.values()))
        if query_norm == 0:
            return []

        scores: dict[str, float] = defaultdict(float)
        for term, query_weight in query_weights.items():
            idf = self._idf(term)
            for doc_id, tf in self.postings[term].items():
                document_weight = (1.0 + math.log(tf)) * idf
                scores[doc_id] += query_weight * document_weight

        ranked = sorted(
            (
                SearchResult(doc_id, self.documents[doc_id].title,
                             score / (query_norm * self.document_norms[doc_id]))
                for doc_id, score in scores.items()
            ),
            key=lambda item: (-item.score, item.doc_id),
        )
        return ranked[:top_k]

    def save(self, path: Path) -> None:
        payload = {
            "documents": [asdict(document) for document in self.documents.values()],
            "postings": self.postings,
            "document_frequency": self.document_frequency,
            "document_norms": self.document_norms,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, help="Path to CISI.ALL; sample data is used if omitted")
    parser.add_argument("--query", required=True, help="Natural-language query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    documents = parse_cisi_records(args.corpus) if args.corpus else load_sample_documents(base / "data/sample_documents.json")
    index = TfidfIndex(documents)
    print(f"Indexed {len(documents)} documents; vocabulary={index.vocabulary_size}")
    print(f"Query: {args.query}\n")
    for rank, result in enumerate(index.search(args.query, args.top_k), start=1):
        print(f"{rank:>2}. {result.doc_id:<5} score={result.score:.4f}  {result.title}")


if __name__ == "__main__":
    main()


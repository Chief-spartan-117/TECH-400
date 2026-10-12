"""Shared preprocessing plus three interpretable retrieval baselines."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STOP_WORDS = {
    "a", "about", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "between", "both",
    "but", "by", "can", "could", "did", "do", "does", "doing", "during", "each", "few",
    "for", "from", "further", "had", "has", "have", "having", "he", "her", "here",
    "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would",
    "you", "your", "yours", "yourself",
}


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    author: str = ""
    abstract: str = ""

    @property
    def searchable_text(self) -> str:
        # Title repetition is the same modest field boost used in Week 6.
        return f"{self.title} {self.title} {self.author} {self.abstract}"


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    title: str
    score: float


def stem(token: str) -> str:
    """Conservative dependency-free suffix stripping."""
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
    """Normalize, lowercase, tokenize, remove stop words, and stem."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    tokens = re.findall(r"[a-z][a-z0-9-]*", normalized.lower())
    return [stem(token) for token in tokens if token not in STOP_WORDS and len(token) > 1]


def load_documents(path: Path) -> list[Document]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return [Document(item["id"], item["title"], item.get("author", ""), item.get("abstract", "")) for item in records]


def parse_cisi_records(path: Path) -> list[Document]:
    """Read the .I/.T/.A/.W fields from CISI.ALL."""
    documents: list[Document] = []
    current_id = ""
    fields: dict[str, list[str]] = defaultdict(list)
    active_field = ""

    def finish_record() -> None:
        if current_id:
            documents.append(Document(
                current_id,
                " ".join(fields["T"]).strip() or f"Document {current_id}",
                " ".join(fields["A"]).strip(),
                " ".join(fields["W"]).strip(),
            ))

    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            identifier = re.match(r"^\.I\s+(\d+)", line)
            if identifier:
                finish_record()
                current_id = identifier.group(1)
                fields = defaultdict(list)
                active_field = ""
            elif re.match(r"^\.[TAWBX]$", line):
                active_field = line[1]
            elif active_field in {"T", "A", "W"} and line.strip():
                fields[active_field].append(line.strip())
    finish_record()
    return documents


class CorpusStatistics:
    """Build shared term statistics once so model comparisons use identical data."""

    def __init__(self, documents: Iterable[Document]):
        self.documents = {document.doc_id: document for document in documents}
        if not self.documents:
            raise ValueError("At least one document is required")
        self.term_counts = {
            doc_id: Counter(preprocess(document.searchable_text))
            for doc_id, document in self.documents.items()
        }
        self.lengths = {doc_id: sum(counts.values()) for doc_id, counts in self.term_counts.items()}
        self.average_length = sum(self.lengths.values()) / len(self.lengths)
        self.postings: dict[str, dict[str, int]] = defaultdict(dict)
        self.document_frequency: Counter[str] = Counter()
        for doc_id, counts in self.term_counts.items():
            for term, frequency in counts.items():
                self.postings[term][doc_id] = frequency
                self.document_frequency[term] += 1

    @property
    def vocabulary_size(self) -> int:
        return len(self.postings)


class RetrievalModel:
    name = "base"

    def __init__(self, corpus: CorpusStatistics):
        self.corpus = corpus

    def _rank(self, scores: dict[str, float], top_k: int) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]
        return [SearchResult(doc_id, self.corpus.documents[doc_id].title, score) for doc_id, score in ranked if score > 0]

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        raise NotImplementedError


class BinaryOverlapModel(RetrievalModel):
    """Baseline: rank by the fraction of unique query terms present."""

    name = "Binary overlap"

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        terms = set(preprocess(query))
        if not terms:
            return []
        scores: dict[str, float] = defaultdict(float)
        for term in terms:
            for doc_id in self.corpus.postings.get(term, {}):
                scores[doc_id] += 1.0 / len(terms)
        return self._rank(scores, top_k)


class TfidfCosineModel(RetrievalModel):
    """Week 6 model: logarithmic TF–IDF with cosine normalization."""

    name = "TF-IDF cosine"

    def __init__(self, corpus: CorpusStatistics):
        super().__init__(corpus)
        self.document_norms = {
            doc_id: math.sqrt(sum(((1 + math.log(tf)) * self._idf(term)) ** 2 for term, tf in counts.items())) or 1.0
            for doc_id, counts in corpus.term_counts.items()
        }

    def _idf(self, term: str) -> float:
        n = len(self.corpus.documents)
        return math.log((n + 1) / (self.corpus.document_frequency.get(term, 0) + 1)) + 1.0

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_counts = Counter(preprocess(query))
        query_weights = {
            term: (1 + math.log(tf)) * self._idf(term)
            for term, tf in query_counts.items() if term in self.corpus.postings
        }
        query_norm = math.sqrt(sum(weight * weight for weight in query_weights.values()))
        if not query_norm:
            return []
        scores: dict[str, float] = defaultdict(float)
        for term, query_weight in query_weights.items():
            idf = self._idf(term)
            for doc_id, frequency in self.corpus.postings[term].items():
                scores[doc_id] += query_weight * (1 + math.log(frequency)) * idf
        normalized = {
            doc_id: score / (query_norm * self.document_norms[doc_id])
            for doc_id, score in scores.items()
        }
        return self._rank(normalized, top_k)


class BM25Model(RetrievalModel):
    """Okapi BM25 with conventional k1=1.5 and b=0.75 parameters."""

    name = "BM25"

    def __init__(self, corpus: CorpusStatistics, k1: float = 1.5, b: float = 0.75):
        super().__init__(corpus)
        self.k1 = k1
        self.b = b

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_counts = Counter(preprocess(query))
        scores: dict[str, float] = defaultdict(float)
        n = len(self.corpus.documents)
        for term, query_frequency in query_counts.items():
            df = self.corpus.document_frequency.get(term, 0)
            if not df:
                continue
            # The +1 form keeps IDF positive for terms appearing in many documents.
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for doc_id, frequency in self.corpus.postings[term].items():
                length_ratio = self.corpus.lengths[doc_id] / self.corpus.average_length
                denominator = frequency + self.k1 * (1 - self.b + self.b * length_ratio)
                term_score = idf * frequency * (self.k1 + 1) / denominator
                scores[doc_id] += query_frequency * term_score
        return self._rank(scores, top_k)


def create_models(documents: Iterable[Document]) -> list[RetrievalModel]:
    corpus = CorpusStatistics(documents)
    return [BinaryOverlapModel(corpus), TfidfCosineModel(corpus), BM25Model(corpus)]


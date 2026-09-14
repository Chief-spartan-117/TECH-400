"""
ir_system.py
------------
A basic Information Retrieval (IR) system built around an inverted index and
Boolean retrieval, for a small collection of 5-10 text documents.

Core pieces:
    - Document ingestion   (add_document / add_documents_from_folder)
    - Dictionary            (the set of all distinct terms in the collection)
    - Inverted index        (term -> sorted set of document IDs containing it)
    - Boolean query engine   (supports AND, OR, NOT, with left-to-right
                              evaluation and optional parentheses)

Design choices are explained in the accompanying report (report.docx).
"""

from __future__ import annotations
import os
import re
import string
from collections import defaultdict
from typing import Dict, List, Set


class IRSystem:
    def __init__(self):
        # doc_id (int) -> raw text (str), in insertion order
        self.documents: Dict[int, str] = {}
        # doc_id (int) -> human-readable name (e.g. filename)
        self.doc_names: Dict[int, str] = {}
        # term (str) -> set of doc_ids containing that term
        self.inverted_index: Dict[str, Set[int]] = defaultdict(set)
        self._next_id = 0

    # ------------------------------------------------------------------ #
    # 1. Document ingestion
    # ------------------------------------------------------------------ #
    def add_document(self, text: str, name: str | None = None) -> int:
        """Add a single document to the collection and update the index.

        Returns the assigned document id.
        """
        doc_id = self._next_id
        self._next_id += 1
        self.documents[doc_id] = text
        self.doc_names[doc_id] = name if name else f"doc{doc_id}"

        for term in self._tokenize(text):
            self.inverted_index[term].add(doc_id)

        return doc_id

    def add_documents_from_folder(self, folder_path: str) -> None:
        """Add every .txt file found in a folder, sorted by filename so the
        result is deterministic."""
        filenames = sorted(f for f in os.listdir(folder_path) if f.endswith(".txt"))
        for filename in filenames:
            path = os.path.join(folder_path, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.add_document(text, name=filename)

    # ------------------------------------------------------------------ #
    # 2. Tokenization / normalization
    # ------------------------------------------------------------------ #
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Lowercase, strip punctuation, and split into word tokens.

        Kept intentionally simple (no stemming, no stopword removal) so the
        index and query results stay easy to trace by hand -- see the
        report for the reasoning behind this choice.
        """
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return re.findall(r"[a-z0-9]+", text)

    # ------------------------------------------------------------------ #
    # 3. Dictionary
    # ------------------------------------------------------------------ #
    def get_dictionary(self) -> List[str]:
        """Return the sorted list of all distinct terms in the collection."""
        return sorted(self.inverted_index.keys())

    # ------------------------------------------------------------------ #
    # 4. Inverted index access
    # ------------------------------------------------------------------ #
    def get_postings(self, term: str) -> Set[int]:
        """Return the set of doc_ids containing `term` (empty set if absent)."""
        return set(self.inverted_index.get(term.lower(), set()))

    def print_index(self) -> None:
        print(f"{'Term':<15} Postings (doc ids)")
        print("-" * 40)
        for term in self.get_dictionary():
            postings = sorted(self.inverted_index[term])
            print(f"{term:<15} {postings}")

    # ------------------------------------------------------------------ #
    # 5. Boolean retrieval
    # ------------------------------------------------------------------ #
    def search(self, query: str) -> Set[int]:
        """Evaluate a Boolean query and return the matching set of doc_ids.

        Supported syntax:
            term1 AND term2
            term1 OR term2
            NOT term1
            term1 AND NOT term2
            (term1 OR term2) AND term3

        Operators are case-insensitive keywords (AND / OR / NOT); everything
        else is treated as a single-word query term. Evaluation is a small
        recursive-descent parser with standard precedence: NOT > AND > OR.
        """
        tokens = self._tokenize_query(query)
        self._pos = 0
        self._tokens = tokens
        result = self._parse_or()
        return result

    # -- query tokenizer: keeps parentheses and operators as separate tokens
    @staticmethod
    def _tokenize_query(query: str) -> List[str]:
        query = query.replace("(", " ( ").replace(")", " ) ")
        return query.split()

    def _all_doc_ids(self) -> Set[int]:
        return set(self.documents.keys())

    def _peek(self) -> str | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    # OR has lowest precedence
    def _parse_or(self) -> Set[int]:
        result = self._parse_and()
        while self._peek() and self._peek().upper() == "OR":
            self._advance()
            rhs = self._parse_and()
            result = result | rhs
        return result

    def _parse_and(self) -> Set[int]:
        result = self._parse_not()
        while self._peek() and self._peek().upper() == "AND":
            self._advance()
            rhs = self._parse_not()
            result = result & rhs
        return result

    def _parse_not(self) -> Set[int]:
        if self._peek() and self._peek().upper() == "NOT":
            self._advance()
            operand = self._parse_not()
            return self._all_doc_ids() - operand
        return self._parse_atom()

    def _parse_atom(self) -> Set[int]:
        tok = self._peek()
        if tok == "(":
            self._advance()  # consume '('
            result = self._parse_or()
            if self._peek() == ")":
                self._advance()  # consume ')'
            return result
        else:
            term = self._advance()
            return self.get_postings(term)


if __name__ == "__main__":
    # Minimal smoke test when run directly.
    ir = IRSystem()
    ir.add_documents_from_folder(os.path.join(os.path.dirname(__file__), "docs"))
    ir.print_index()

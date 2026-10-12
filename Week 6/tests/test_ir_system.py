import json
import tempfile
import unittest
from pathlib import Path

from ir_system import Document, TfidfIndex, parse_cisi_records, preprocess


class PreprocessingTests(unittest.TestCase):
    def test_normalizes_filters_and_stems(self):
        tokens = preprocess("The Libraries are INDEXING documents!")
        self.assertNotIn("the", tokens)
        self.assertIn("library", tokens)
        self.assertIn("index", tokens)


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.documents = [
            Document("1", "Library indexing", abstract="Automatic indexing and retrieval"),
            Document("2", "Building design", abstract="Architecture for university buildings"),
            Document("3", "Retrieval evaluation", abstract="Precision and recall for search"),
        ]
        self.index = TfidfIndex(self.documents)

    def test_relevant_document_ranks_first(self):
        result = self.index.search("automatic document indexing", top_k=2)
        self.assertEqual(result[0].doc_id, "1")

    def test_unknown_query_returns_empty_list(self):
        self.assertEqual(self.index.search("xylophone", top_k=5), [])

    def test_rejects_invalid_top_k(self):
        with self.assertRaises(ValueError):
            self.index.search("indexing", top_k=0)

    def test_saved_index_is_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "index.json"
            self.index.save(path)
            payload = json.loads(path.read_text())
            self.assertEqual(len(payload["documents"]), 3)
            self.assertIn("index", payload["postings"])


class ParserTests(unittest.TestCase):
    def test_parses_cisi_fields(self):
        content = ".I 7\n.T\nA title\n.A\nAn author\n.W\nAbstract text.\n.X\n1 1 1\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "CISI.ALL"
            path.write_text(content)
            documents = parse_cisi_records(path)
        self.assertEqual(documents[0].doc_id, "7")
        self.assertEqual(documents[0].title, "A title")
        self.assertEqual(documents[0].abstract, "Abstract text.")


if __name__ == "__main__":
    unittest.main()


import unittest

from evaluate_models import calculate_metrics
from retrieval_models import BM25Model, BinaryOverlapModel, CorpusStatistics, Document, TfidfCosineModel


class MetricTests(unittest.TestCase):
    def test_known_ranking_metrics(self):
        # Relevant documents occur at ranks 1 and 3.
        result = calculate_metrics(["A", "X", "B", "Y"], {"A", "B"}, k=3)
        self.assertAlmostEqual(result["precision"], 2 / 3)
        self.assertAlmostEqual(result["recall"], 1.0)
        self.assertAlmostEqual(result["ap"], (1.0 + 2 / 3) / 2)
        self.assertAlmostEqual(result["rr"], 1.0)
        expected_ndcg = (1 + 1 / 2) / (1 + 1 / 1.584962500721156)
        self.assertAlmostEqual(result["ndcg"], expected_ndcg)

    def test_no_relevant_documents_returns_zeroes(self):
        result = calculate_metrics(["A"], set(), k=1)
        self.assertTrue(all(value == 0.0 for value in result.values()))

    def test_missing_relevant_document_reduces_average_precision(self):
        result = calculate_metrics(["A", "X"], {"A", "B"}, k=2)
        self.assertAlmostEqual(result["ap"], 0.5)
        self.assertAlmostEqual(result["recall"], 0.5)

    def test_invalid_cutoff_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_metrics(["A"], {"A"}, k=0)


class RetrievalModelTests(unittest.TestCase):
    def setUp(self):
        documents = [
            Document("D1", "Automatic indexing", abstract="indexing documents for retrieval"),
            Document("D2", "Library building", abstract="architecture and university planning"),
            Document("D3", "Retrieval metrics", abstract="precision recall evaluation"),
        ]
        corpus = CorpusStatistics(documents)
        self.models = [BinaryOverlapModel(corpus), TfidfCosineModel(corpus), BM25Model(corpus)]

    def test_all_models_rank_obvious_match_first(self):
        for model in self.models:
            with self.subTest(model=model.name):
                self.assertEqual(model.search("automatic document indexing", 3)[0].doc_id, "D1")

    def test_all_models_return_empty_for_unknown_terms(self):
        for model in self.models:
            with self.subTest(model=model.name):
                self.assertEqual(model.search("xylophone", 3), [])

    def test_all_models_reject_invalid_top_k(self):
        for model in self.models:
            with self.subTest(model=model.name):
                with self.assertRaises(ValueError):
                    model.search("indexing", 0)


if __name__ == "__main__":
    unittest.main()


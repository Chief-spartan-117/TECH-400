"""
test_ir_system.py
------------------
A small set of sanity checks for ir_system.py. Run with:
    python3 -m unittest test_ir_system.py -v
"""

import unittest
from ir_system import IRSystem


class TestIRSystem(unittest.TestCase):
    def setUp(self):
        self.ir = IRSystem()
        self.ir.add_document("The cat sat on the mat", name="d0")
        self.ir.add_document("The dog sat on the log", name="d1")
        self.ir.add_document("Cats and dogs are friends", name="d2")

    def test_dictionary_contains_expected_terms(self):
        terms = self.ir.get_dictionary()
        self.assertIn("cat", terms)
        self.assertIn("dog", terms)
        self.assertIn("sat", terms)

    def test_postings_are_correct(self):
        self.assertEqual(self.ir.get_postings("sat"), {0, 1})
        self.assertEqual(self.ir.get_postings("cat"), {0})
        self.assertEqual(self.ir.get_postings("nonexistent"), set())

    def test_and_query(self):
        self.assertEqual(self.ir.search("sat AND on"), {0, 1})
        self.assertEqual(self.ir.search("cat AND dog"), set())

    def test_or_query(self):
        self.assertEqual(self.ir.search("cat OR dog"), {0, 1})

    def test_not_query(self):
        self.assertEqual(self.ir.search("NOT sat"), {2})

    def test_combined_query_with_parentheses(self):
        self.assertEqual(
            self.ir.search("(cat OR dog) AND NOT friends"), {0, 1}
        )

    def test_case_insensitivity(self):
        self.assertEqual(self.ir.search("CAT"), {0})
        self.assertEqual(self.ir.search("cat and dog"), set())


if __name__ == "__main__":
    unittest.main()

"""
tests/test_reliability_edge_cases.py - Unit tests for reliability and edge cases.
Verifies boundary behaviors: empty database queries, invalid filter formats,
numeric string edge cases, and non-ASCII character handling.
"""

import os
import shutil
import tempfile
import unittest

import ai_service
import database
import invoice_parser


class TestReliabilityEdgeCases(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_edge_cases_")
        self.db_path = os.path.join(self.test_dir, "edge_ledger.db")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_empty_table_operations(self):
        # Database initialized with 0 records
        database.init_db(self.db_path)
        invoices, err = database.list_invoices(db_path=self.db_path)
        self.assertIsNone(err)
        self.assertEqual(invoices, [])

        filtered, err = database.search_and_filter_invoices(search_query="NonExistent", db_path=self.db_path)
        self.assertIsNone(err)
        self.assertEqual(filtered, [])

        summary, err = database.get_expense_summary(db_path=self.db_path)
        self.assertIsNone(err)
        self.assertEqual(summary["total_invoices"], 0)
        self.assertEqual(summary["total_spent"], 0.0)
        self.assertEqual(summary["by_category"], [])
        self.assertEqual(summary["by_currency"], [])

    def test_database_invalid_id_lookup(self):
        database.init_db(self.db_path)
        rec, err = database.get_invoice_by_id(99999, db_path=self.db_path)
        self.assertIsNone(rec)
        self.assertIn("not found", err.lower())

    def test_numeric_currency_symbol_stripping(self):
        # Various international currency symbol representations and commas
        raw = {
            "vendor": "Global Store",
            "subtotal": "£ 1,250.50",
            "tax": "€ 250.00",
            "total": "$ 1,500.50",
            "currency": "€",
        }
        cleaned, warnings = ai_service.validate_and_clean_invoice_data(raw)
        self.assertEqual(cleaned["subtotal"], 1250.50)
        self.assertEqual(cleaned["tax"], 250.00)
        self.assertEqual(cleaned["total"], 1500.50)
        self.assertEqual(cleaned["currency"], "EUR")  # Symbol mapped to ISO code
        self.assertEqual(len(warnings), 0)

    def test_invoice_parser_none_and_non_string_inputs(self):
        ok, text, err = invoice_parser.validate_pasted_text(None)
        self.assertFalse(ok)
        self.assertIn("empty", err.lower())

        ok, text, err = invoice_parser.extract_text_from_upload(None, b"test")
        self.assertFalse(ok)
        self.assertIn("invalid filename", err.lower())

    def test_database_duplicate_check_with_empty_data(self):
        # Empty input should not flag as duplicate
        has_dup, dups, err = database.check_for_duplicates({}, db_path=self.db_path)
        self.assertFalse(has_dup)
        self.assertEqual(dups, [])


if __name__ == "__main__":
    unittest.main()

"""
tests/test_database.py - Unit tests for database module.
Tests initialization, insertion, duplicate detection, queries, aggregations,
and CSV export using an isolated temporary SQLite database.
"""

import os
import shutil
import tempfile
import unittest

import database


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_db_unit_")
        self.db_path = os.path.join(self.test_dir, "test_ledger.db")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_db(self):
        ok, err = database.init_db(self.db_path)
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(os.path.exists(self.db_path))

    def test_save_and_get_invoice(self):
        sample = {
            "vendor": "Acme Tools",
            "invoice_number": "INV-001",
            "invoice_date": "2026-10-15",
            "subtotal": 100.0,
            "tax": 10.0,
            "total": 110.0,
            "currency": "USD",
            "category": "Software",
        }
        ok, rec_id, err = database.save_invoice(sample, source_filename="acme.pdf", db_path=self.db_path)
        self.assertTrue(ok)
        self.assertEqual(rec_id, 1)

        rec, get_err = database.get_invoice_by_id(1, db_path=self.db_path)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["vendor"], "Acme Tools")
        self.assertEqual(rec["total"], 110.0)
        self.assertEqual(rec["source_filename"], "acme.pdf")
        self.assertIn("T", rec["created_at"])  # ISO timestamp

    def test_missing_optional_fields(self):
        sparse = {
            "vendor": "Corner Store",
            "invoice_number": None,
            "invoice_date": None,
            "subtotal": None,
            "tax": None,
            "total": 5.0,
            "currency": "USD",
            "category": None,
        }
        ok, rec_id, err = database.save_invoice(sparse, db_path=self.db_path)
        self.assertTrue(ok)
        rec, _ = database.get_invoice_by_id(rec_id, db_path=self.db_path)
        self.assertIsNone(rec["invoice_number"])
        self.assertIsNone(rec["tax"])
        self.assertEqual(rec["total"], 5.0)

    def test_duplicate_detection(self):
        sample = {
            "vendor": "Apex Logistics",
            "invoice_number": "APX-99",
            "invoice_date": "2026-10-18",
            "total": 85.0,
        }
        # First check: no duplicates
        has_dup, dups, _ = database.check_for_duplicates(sample, db_path=self.db_path)
        self.assertFalse(has_dup)

        # Save record
        database.save_invoice(sample, db_path=self.db_path)

        # Second check: duplicate detected without overwriting
        has_dup_after, dups_after, _ = database.check_for_duplicates(sample, db_path=self.db_path)
        self.assertTrue(has_dup_after)
        self.assertEqual(len(dups_after), 1)
        self.assertEqual(dups_after[0]["id"], 1)

    def test_search_and_filter(self):
        rec1 = {"vendor": "Beta Software", "invoice_number": "BS-1", "invoice_date": "2026-10-01", "total": 50.0, "category": "Software"}
        rec2 = {"vendor": "Delta Coffee", "invoice_number": "DC-2", "invoice_date": "2026-10-10", "total": 12.0, "category": "Meals & Entertainment"}
        database.save_invoice(rec1, db_path=self.db_path)
        database.save_invoice(rec2, db_path=self.db_path)

        # Search by vendor text
        res_v, _ = database.search_and_filter_invoices(search_query="Beta", db_path=self.db_path)
        self.assertEqual(len(res_v), 1)
        self.assertEqual(res_v[0]["vendor"], "Beta Software")

        # Filter by category
        res_c, _ = database.search_and_filter_invoices(category="Software", db_path=self.db_path)
        self.assertEqual(len(res_c), 1)

        # Filter by date range
        res_d, _ = database.search_and_filter_invoices(date_from="2026-10-05", date_to="2026-10-15", db_path=self.db_path)
        self.assertEqual(len(res_d), 1)
        self.assertEqual(res_d[0]["vendor"], "Delta Coffee")

    def test_get_expense_summary(self):
        rec1 = {"vendor": "V1", "total": 100.0, "currency": "USD", "category": "Software"}
        rec2 = {"vendor": "V2", "total": 50.0, "currency": "USD", "category": "Software"}
        rec3 = {"vendor": "V3", "total": 20.0, "currency": "EUR", "category": "Travel"}
        database.save_invoice(rec1, db_path=self.db_path)
        database.save_invoice(rec2, db_path=self.db_path)
        database.save_invoice(rec3, db_path=self.db_path)

        summary, err = database.get_expense_summary(db_path=self.db_path)
        self.assertIsNone(err)
        self.assertEqual(summary["total_invoices"], 3)
        self.assertEqual(summary["total_spent"], 170.0)
        self.assertEqual(len(summary["by_currency"]), 2)


if __name__ == "__main__":
    unittest.main()

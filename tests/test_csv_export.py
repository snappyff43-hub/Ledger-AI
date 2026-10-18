"""
tests/test_csv_export.py - Unit tests for safe CSV export in database module.
Tests column headers, expected values, formula injection mitigation, Unicode,
and handling of empty datasets.
"""

import unittest

import database


class TestCSVExport(unittest.TestCase):

    def test_export_invoices_to_csv_headers_and_values(self):
        records = [
            {
                "id": 1,
                "vendor": "Alpha Tech",
                "invoice_number": "INV-100",
                "invoice_date": "2026-10-18",
                "subtotal": 100.0,
                "tax": 10.0,
                "total": 110.0,
                "currency": "USD",
                "category": "Software",
                "source_filename": "inv.pdf",
                "created_at": "2026-10-18T12:00:00",
            }
        ]
        ok, csv_str, err = database.export_invoices_to_csv(records)
        self.assertTrue(ok)
        self.assertIsNone(err)

        # Check headers
        self.assertIn("Vendor,Invoice Number,Date,Subtotal,Tax,Total,Currency,Category,Source File,Recorded At", csv_str)
        # Check row content
        self.assertIn("Alpha Tech,INV-100,2026-10-18,100.0,10.0,110.0,USD,Software,inv.pdf,2026-10-18T12:00:00", csv_str)

    def test_export_invoices_to_csv_empty_list(self):
        ok, csv_str, err = database.export_invoices_to_csv([])
        self.assertTrue(ok)
        self.assertIsNone(err)
        # Should contain header only
        lines = [line.strip() for line in csv_str.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("Vendor", lines[0])

    def test_export_invoices_to_csv_formula_injection_defense(self):
        # Cells starting with =, +, -, @ must be prepended with '
        nasty_records = [
            {
                "id": 2,
                "vendor": "=CMD('calc')",
                "invoice_number": "+12345",
                "invoice_date": "-2026",
                "category": "@Admin",
                "total": 10.0,
            }
        ]
        ok, csv_str, err = database.export_invoices_to_csv(nasty_records)
        self.assertTrue(ok)
        self.assertIn("'=CMD('calc')", csv_str)
        self.assertIn("'+12345", csv_str)
        self.assertIn("'-2026", csv_str)
        self.assertIn("'@Admin", csv_str)

    def test_export_invoices_to_csv_unicode_and_quotes(self):
        records = [
            {
                "id": 3,
                "vendor": "Bürobedarf GmbH",
                "category": 'Office "Supplies" & More',
                "total": 25.50,
            }
        ]
        ok, csv_str, err = database.export_invoices_to_csv(records)
        self.assertTrue(ok)
        self.assertIn("Bürobedarf GmbH", csv_str)
        self.assertIn('"Office ""Supplies"" & More"', csv_str)


if __name__ == "__main__":
    unittest.main()

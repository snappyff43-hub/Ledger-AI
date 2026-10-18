"""
tests/test_invoice_parser.py - Unit tests for invoice_parser module.
Tests pasted text validation, TXT/PDF file extraction, size limits, and empty/malformed handling.
"""

import io
import unittest
from pypdf import PdfWriter

import invoice_parser


class TestInvoiceParser(unittest.TestCase):

    def test_validate_pasted_text_valid(self):
        sample = "   Vendor: CloudCorp\nTotal: $100.00   "
        ok, cleaned, err = invoice_parser.validate_pasted_text(sample)
        self.assertTrue(ok)
        self.assertEqual(cleaned, "Vendor: CloudCorp\nTotal: $100.00")
        self.assertIsNone(err)

    def test_validate_pasted_text_empty_and_whitespace(self):
        for empty_val in ("", "   ", "\t\n  \r"):
            ok, cleaned, err = invoice_parser.validate_pasted_text(empty_val)
            self.assertFalse(ok)
            self.assertEqual(cleaned, "")
            self.assertIsNotNone(err)

    def test_extract_text_from_txt_valid(self):
        txt_bytes = "Vendor: FastHost\nTotal: 50.00 USD".encode("utf-8")
        ok, text, err = invoice_parser.extract_text_from_txt(txt_bytes)
        self.assertTrue(ok)
        self.assertIn("FastHost", text)
        self.assertIsNone(err)

    def test_extract_text_from_txt_empty(self):
        ok, text, err = invoice_parser.extract_text_from_txt(b"")
        self.assertFalse(ok)
        self.assertIn("empty", err.lower())

    def test_extract_text_from_txt_oversized(self):
        oversized = b"A" * (5 * 1024 * 1024 + 10)
        ok, text, err = invoice_parser.extract_text_from_txt(oversized)
        self.assertFalse(ok)
        self.assertIn("exceeds", err.lower())

    def test_extract_text_from_pdf_empty_and_scanned(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        stream = io.BytesIO()
        writer.write(stream)
        ok, text, err = invoice_parser.extract_text_from_pdf(stream.getvalue())
        self.assertFalse(ok)
        self.assertIn("scanned", err.lower())

    def test_extract_text_from_pdf_malformed(self):
        corrupted = b"%PDF-1.4 malformed corrupted binary data"
        ok, text, err = invoice_parser.extract_text_from_pdf(corrupted)
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_extract_text_from_upload_unsupported_extension(self):
        ok, text, err = invoice_parser.extract_text_from_upload("invoice.docx", b"dummy")
        self.assertFalse(ok)
        self.assertIn("unsupported", err.lower())

    def test_extract_text_from_upload_path_sanitization(self):
        txt_bytes = b"Vendor: SafeCorp\nTotal: 10.00"
        ok, text, err = invoice_parser.extract_text_from_upload("../../traversal/inv.txt", txt_bytes)
        self.assertTrue(ok)
        self.assertIn("SafeCorp", text)


if __name__ == "__main__":
    unittest.main()

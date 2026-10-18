"""
tests/test_ai_service.py - Unit tests for ai_service module.
Tests canonical schema validation, zero-value preservation, arithmetic checks,
offline error handling, and mock model response parsing without external API calls.
"""

import unittest
from unittest.mock import patch

import ai_service


class TestAIService(unittest.TestCase):

    def test_validate_and_clean_valid_invoice(self):
        data = {
            "vendor": "Acme Cloud",
            "invoice_number": "INV-101",
            "invoice_date": "2026-10-18",
            "subtotal": 100.0,
            "tax": 10.0,
            "total": 110.0,
            "currency": "USD",
            "category": "Software",
        }
        cleaned, warnings = ai_service.validate_and_clean_invoice_data(data)
        self.assertEqual(cleaned["vendor"], "Acme Cloud")
        self.assertEqual(cleaned["total"], 110.0)
        self.assertEqual(len(warnings), 0)

    def test_validate_and_clean_preserves_legitimate_zeros(self):
        data = {"vendor": "Zero Tax Corp", "subtotal": 0.0, "tax": 0.0, "total": 0.0}
        cleaned, warnings = ai_service.validate_and_clean_invoice_data(data)
        self.assertEqual(cleaned["subtotal"], 0.0)
        self.assertEqual(cleaned["tax"], 0.0)
        self.assertEqual(cleaned["total"], 0.0)

    def test_validate_and_clean_missing_fields_become_none(self):
        data = {"vendor": "unknown", "invoice_number": "null", "invoice_date": "N/A", "total": "none"}
        cleaned, warnings = ai_service.validate_and_clean_invoice_data(data)
        self.assertIsNone(cleaned["vendor"])
        self.assertIsNone(cleaned["invoice_number"])
        self.assertIsNone(cleaned["invoice_date"])
        self.assertIsNone(cleaned["total"])

    def test_validate_and_clean_arithmetic_discrepancy_warning(self):
        data = {"vendor": "Store", "subtotal": 50.0, "tax": 5.0, "total": 80.0}
        cleaned, warnings = ai_service.validate_and_clean_invoice_data(data)
        self.assertEqual(cleaned["subtotal"], 50.0)
        self.assertEqual(cleaned["total"], 80.0)  # Preserved without silent alteration
        self.assertTrue(any("Arithmetic discrepancy" in w for w in warnings))

    def test_validate_and_clean_negative_credit_note_warning(self):
        data = {"vendor": "Refund Corp", "total": -45.0}
        cleaned, warnings = ai_service.validate_and_clean_invoice_data(data)
        self.assertEqual(cleaned["total"], -45.0)
        self.assertTrue(any("negative" in w for w in warnings))

    def test_parse_and_validate_extraction_markdown_codeblock(self):
        raw_json_str = "```json\n{\"vendor\": \"Markdown Corp\", \"total\": 99.0}\n```"
        success, cleaned, err = ai_service.parse_and_validate_extraction(raw_json_str)
        self.assertTrue(success)
        self.assertEqual(cleaned["vendor"], "Markdown Corp")
        self.assertEqual(cleaned["total"], 99.0)

    def test_parse_and_validate_extraction_malformed_json(self):
        malformed = "This is not valid JSON content"
        success, cleaned, err = ai_service.parse_and_validate_extraction(malformed)
        self.assertFalse(success)
        self.assertIn("not valid json", err.lower())

    def test_offline_ollama_graceful_error(self):
        # Point to an unallocated port to guarantee offline connection failure
        with patch.object(ai_service, "DEFAULT_OLLAMA_URL", "http://127.0.0.1:59999"):
            is_alive, msg = ai_service.check_ollama_status(base_url="http://127.0.0.1:59999")
            self.assertFalse(is_alive)
            self.assertIn("could not connect", msg.lower())

            ok, data, err = ai_service.extract_invoice_data("Sample invoice", base_url="http://127.0.0.1:59999")
            self.assertFalse(ok)
            self.assertIn("connection check failed", err.lower())


if __name__ == "__main__":
    unittest.main()

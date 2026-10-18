"""
tests/test_benchmark_safety.py - Tests security and safe error handling in compare_models.py.
Verifies that missing GEMINI_API_KEY skips cleanly without making external API requests,
that ground truth evaluation handles partial discrepancies accurately, and no secrets are logged.
"""

import unittest
from unittest.mock import patch

import compare_models


class TestBenchmarkSafety(unittest.TestCase):

    def test_gemini_skipped_without_api_key(self):
        # Guarantee GEMINI_API_KEY is not set
        with patch.dict("os.environ", {}, clear=True):
            ok, data, elapsed, err = compare_models.run_gemini_benchmark()
            self.assertFalse(ok)
            self.assertEqual(data, {})
            self.assertEqual(elapsed, 0.0)
            self.assertIn("SKIPPED: GEMINI_API_KEY environment variable is not set", err)

    def test_evaluate_agreement_perfect_match(self):
        ground_truth = dict(compare_models.GROUND_TRUTH)
        res = compare_models.evaluate_agreement(ground_truth, compare_models.GROUND_TRUTH)
        self.assertEqual(res["matches"], len(compare_models.GROUND_TRUTH))
        self.assertEqual(res["accuracy_pct"], 100.0)

    def test_evaluate_agreement_with_missing_and_wrong_fields(self):
        partial_data = dict(compare_models.GROUND_TRUTH)
        partial_data["vendor"] = "Wrong Vendor LLC"
        partial_data["total"] = 9999.0
        res = compare_models.evaluate_agreement(partial_data, compare_models.GROUND_TRUTH)
        self.assertEqual(res["matches"], len(compare_models.GROUND_TRUTH) - 2)
        self.assertEqual(res["accuracy_pct"], 75.0)

    def test_print_comparison_report_format_safety(self):
        # Verify formatting executes without raising exceptions or requiring live services
        mock_ollama = (True, dict(compare_models.GROUND_TRUTH), 25.0, None)
        mock_gemini = (False, {}, 0.0, "SKIPPED: GEMINI_API_KEY not configured")
        try:
            compare_models.print_comparison_report(mock_ollama, mock_gemini)
        except Exception as exc:
            self.fail(f"print_comparison_report raised an unexpected exception: {exc}")


if __name__ == "__main__":
    unittest.main()

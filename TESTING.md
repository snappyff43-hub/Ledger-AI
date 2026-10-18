# LocalLedger AI — Automated Testing & Regression Documentation

This document describes the automated test architecture, test modules, and verification instructions for **LocalLedger AI**.

---

## 1. Test Architecture & Design Principles

The automated test suite uses Python's standard `unittest` framework to ensure that tests run fast, reliably, and independently of external dependencies:
- **100% Synthetic & Privacy-Compliant:** Uses exclusively fictional invoice data (e.g. `Acme Tools`, `Apex Logistics`). Never accesses real financial records or customer documents.
- **Isolated SQLite Storage:** Database tests create and clean up temporary database files in disposable system temp directories (`tempfile.mkdtemp`), leaving the production ledger (`data/ledger.db`) completely untouched.
- **Mocked & Offline Safe:** External services (such as Ollama or Gemini) are mocked or safely checked without blocking or requiring live network requests. Tests execute completely offline.
- **Zero Secret Exposure:** Benchmark tests verify that missing API keys gracefully skip without throwing unhandled exceptions or logging secrets.

---

## 2. Test Modules Overview

The tests are located in [`tests/`](file:///e:/Hacktoberweek2/localledger_ai/tests):

| Test Module | Area Tested | Key Scenarios Verified |
| :--- | :--- | :--- |
| [`tests/test_invoice_parser.py`](file:///e:/Hacktoberweek2/localledger_ai/tests/test_invoice_parser.py) | Document Parsing | • Pasted text validation & whitespace trimming.<br>• Valid TXT decoding & empty/oversized file rejection (5 MB limit).<br>• In-memory text PDF extraction & scanned PDF detection.<br>• Path traversal sanitization & unsupported file type rejection. |
| [`tests/test_database.py`](file:///e:/Hacktoberweek2/localledger_ai/tests/test_database.py) | SQLite Ledger | • Automatic schema initialization & indexing.<br>• Parameterized insert and query with generated ISO timestamps.<br>• Safe handling of missing optional fields (stored as `None`).<br>• Duplicate detection by `(vendor, invoice_number)` without overwriting.<br>• Search across vendor/invoice #, category filters, and date ranges.<br>• Accurate expense summaries and multi-currency aggregations. |
| [`tests/test_ai_service.py`](file:///e:/Hacktoberweek2/localledger_ai/tests/test_ai_service.py) | AI Extraction & Schema | • Canonical 8-field standardization (`vendor`, `invoice_number`, `invoice_date`, `subtotal`, `tax`, `total`, `currency`, `category`).<br>• Legitimate zero-value preservation (`0.0`).<br>• Missing/placeholder values sanitized to `None`.<br>• Arithmetic discrepancy warnings without mutating invoice values.<br>• Negative amounts flagged as credit note warnings.<br>• Controlled offline error handling for unreachable Ollama service. |
| [`tests/test_csv_export.py`](file:///e:/Hacktoberweek2/localledger_ai/tests/test_csv_export.py) | CSV Generation | • Column headers and record values.<br>• Proper handling of empty invoice lists.<br>• Defense against spreadsheet formula injection (escaping `=, +, -, @`).<br>• UTF-8 Unicode characters and quotes handling. |
| [`tests/test_benchmark_safety.py`](file:///e:/Hacktoberweek2/localledger_ai/tests/test_benchmark_safety.py) | Benchmark Security | • Verifies `compare_models.py` cleanly skips when `GEMINI_API_KEY` is not configured.<br>• Ground-truth field agreement calculations.<br>• Format safety of benchmark reporting without network calls. |
| [`tests/test_reliability_edge_cases.py`](file:///e:/Hacktoberweek2/localledger_ai/tests/test_reliability_edge_cases.py) | Reliability & Boundaries | • Empty database operations & non-existent ID lookup.<br>• International currency symbols & comma formatting.<br>• Non-string / null parser input boundaries.<br>• Duplicate detection with empty input payload. |

---

## 3. How to Run the Automated Tests

From the project root (`E:\Hacktoberweek2\localledger_ai`), run the complete test discovery using the project's virtual environment:

```powershell
cd E:\Hacktoberweek2\localledger_ai
$env:PYTHONPATH="E:\Hacktoberweek2\localledger_ai"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

---

## 4. Actual Test Results

Executed on Python 3.11.9 (`.venv`):
- **Total Tests Discovered:** 36 tests
- **Tests Passed:** 36
- **Tests Failed:** 0
- **Execution Time:** ~4.5 seconds
- **Status:** **OK (100% Passing)**

---

## 5. How to Launch the Application

Once tests are verified, start the Streamlit web interface:

```powershell
cd E:\Hacktoberweek2\localledger_ai
.\.venv\Scripts\streamlit.exe run app.py
```
Open your browser to: **`http://localhost:8501`**

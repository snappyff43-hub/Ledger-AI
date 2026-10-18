# Security & Privacy Policy

LocalLedger AI is built as a local-first application where security, user data sovereignty, and confidentiality are foundational requirements.

---

## 1. Threat Model & Privacy Principles

1. **Zero Data Egress in Core Workflows:**
   - The primary application ([`app.py`](file:///e:/Hacktoberweek2/localledger_ai/app.py)) and extraction pipeline ([`invoice_parser.py`](file:///e:/Hacktoberweek2/localledger_ai/invoice_parser.py), [`ai_service.py`](file:///e:/Hacktoberweek2/localledger_ai/ai_service.py)) interact exclusively with the local Ollama instance on `127.0.0.1:11434`.
   - No invoice text, company names, hourly rates, client information, or tax IDs are ever transmitted across external networks.
2. **Untrusted Input Treatment:**
   - All document text is treated strictly as untrusted data within prompt boundaries. System instructions prevent prompt injection from executing system commands.
3. **Spreadsheet Formula Injection Defense (CSV Injection):**
   - Untrusted text exported to CSV files can execute arbitrary commands in Microsoft Excel or Google Sheets if prefixed with `=`, `+`, `-`, or `@`.
   - [`database.py`](file:///e:/Hacktoberweek2/localledger_ai/database.py) automatically sanitizes all cell contents by prefixing formula characters with an apostrophe (`'`).
4. **Ephemeral Document Handling:**
   - Uploaded PDF and TXT documents are read into RAM buffers using `io.BytesIO`. Uploaded files are never stored in temporary disk caches or database BLOB columns.

---

## 2. Secrets Management & Environment Configuration

- **Never Commit Secrets:** API keys, access tokens, and private credentials must never be committed to Git.
- **Git Hygiene:** [`.gitignore`](file:///e:/Hacktoberweek2/localledger_ai/.gitignore) explicitly excludes:
  - `.env` and `.env.*` (while keeping the safe template `.env.example`).
  - SQLite databases (`*.db`, `*.sqlite`, `data/`).
  - Generated CSV exports and document files (`*.csv`, `*.pdf`, `*.txt`).
- **Benchmark Security:**
  - The developer benchmark script ([`compare_models.py`](file:///e:/Hacktoberweek2/localledger_ai/compare_models.py)) reads credentials exclusively from the `GEMINI_API_KEY` environment variable.
  - Keys are never logged, printed to console, or saved to disk.
  - If the environment variable is absent, the benchmark safely skips cloud evaluation without throwing unhandled exceptions.

---

## 3. Reporting Security Issues

If you discover a security vulnerability or bug related to data protection in LocalLedger AI, please report it privately via GitHub Security Advisories or to the repository maintainer.

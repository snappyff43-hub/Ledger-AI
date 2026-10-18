---
title: "LocalLedger AI — The Zero-Cloud, Privacy-First Invoice Organizer for Freelancers"
published: false
description: "A local-first receipt & invoice organizer running 100% on-device with open-weight Qwen2.5 3B via Ollama, Streamlit, and SQLite."
tags: "opensource, ai, python, productivity, hacktoberfest"
canonical_url: "https://github.com/snappyff43-hub/Ledger-AI"
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

## What I Built

**LocalLedger AI** is a privacy-first, zero-cloud invoice and receipt organizer built specifically for freelancers, independent contractors, and solo founders. 

### The Problem It Solves
Independent operators handle dozens of sensitive invoices, client billing statements, and expense receipts every month. Current options force an unacceptable trade-off:
1. **Cloud Privacy Leaks:** Sending sensitive financial records, private client names, hourly billing rates, and home addresses across cloud AI APIs risks customer confidentiality.
2. **Subscription & Per-Token Overhead:** Commercial SaaS receipt scanners charge recurring monthly fees or per-page API tolls that penalize solo operators for basic bookkeeping.
3. **Manual Transcription Burnout:** Typing dates, invoice IDs, subtotal breakdowns, taxes, and totals into spreadsheets by hand is tedious and error-prone.

### Who Would Pay For It?
- **Freelancers & Independent Developers:** Who bill clients and need clean, categorized expense records for tax write-offs without sending confidential client documents over the internet.
- **Sole Proprietors & Consultants:** Who want a one-click desktop tool that converts messy text or PDFs into spreadsheet-ready CSVs.
- **Commercialization / Side Hustle Potential:** While the core codebase is open-source, the side hustle offering centers on **turnkey setup & customization services** ($49–$99 one-time setup assistance for non-technical small business owners, custom vertical category packs, and turnkey desktop binaries).

---

## Demo

- 🎥 **Video Demo:** [Watch the LocalLedger AI Walkthrough on Google Drive](https://drive.google.com/file/d/1uTFPEZ8HfIOu0nSthFHvDq4_QKxQ2hwa/view?usp=drivesdk)
- **GitHub Repository:** [https://github.com/snappyff43-hub/Ledger-AI](https://github.com/snappyff43-hub/Ledger-AI)
- **Live Local Demo Script:** Available in [`DEMO_GUIDE.md`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/DEMO_GUIDE.md)

### Key Features Demonstrated:
1. **Multi-Input Ingestion:** Accepts pasted text or uploaded text-based PDF/TXT files (with an enforced 5 MB limit).
2. **Deterministic Extraction:** Extracts 8 canonical fields (`vendor`, `invoice_number`, `invoice_date`, `subtotal`, `tax`, `total`, `currency`, `category`) locally.
3. **Anti-Hallucination:** Missing fields evaluate strictly to `null` / empty rather than being fabricated.
4. **Human-in-the-Loop Review:** Pre-filled editable form with arithmetic discrepancy warnings (`subtotal + tax != total`).
5. **Duplicate Protection:** Intercepts repeat scans by `(vendor, invoice_number)` or `(vendor, date, total)` to prevent duplicate accounting entries.
6. **Safe CSV Export:** Exports sanitized records protected against spreadsheet formula injection (`=`, `@`, `+`, `-`).

---

## Code

The complete source code, automated test suite, and architectural documentation are publicly available on GitHub:

{% github snappyff43-hub/Ledger-AI %}

**Repository Details:**
- **URL:** [https://github.com/snappyff43-hub/Ledger-AI](https://github.com/snappyff43-hub/Ledger-AI)
- **Tech Stack:** Python 3.11, Streamlit, Ollama, Qwen2.5 3B, SQLite, `pypdf`.
- **License:** MIT License.

---

## How I Built It

LocalLedger AI was engineered around open-weight models and a strictly local runtime architecture:

1. **Local Inference Engine ([`ai_service.py`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/ai_service.py)):**
   - Utilizes [Ollama](https://ollama.com/) running on `http://127.0.0.1:11434` with **Qwen2.5 3B** (`qwen2.5:3b`, 4-bit quantized `Q4_K_M`).
   - Uses Ollama's native JSON mode (`format: "json"`, `temperature: 0.0`) to guarantee deterministic structured responses matching a strict 8-field canonical schema.
2. **In-Memory Document Pipeline ([`invoice_parser.py`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/invoice_parser.py)):**
   - Uses `pypdf` to extract text in memory without saving uploaded files to disk.
   - Caps text length at 50,000 characters and file sizes at 5 MB to prevent memory exhaustion.
   - Detects scanned image PDFs without a text layer and guides the user to paste text manually.
3. **Local Ledger & Export ([`database.py`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/database.py)):**
   - Uses Python's built-in `sqlite3` (`data/ledger.db`) with parameterized SQL queries.
   - Only confirmed fields, source filenames, and ISO timestamps are saved; raw documents and text are never written to disk.
   - CSV export sanitizes every cell to protect against spreadsheet formula execution exploits.
4. **User Interface ([`app.py`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/app.py)):**
   - Built with Streamlit, featuring a Financial Dashboard, Add & Review Invoice view, and a Searchable Expense History table.
5. **Decoupled Benchmark ([`compare_models.py`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/compare_models.py)):**
   - A standalone developer evaluation tool comparing local Ollama against optional cloud Gemini on a fixed synthetic invoice without coupling cloud dependencies to the core app.

---

## Why Does Open Innovation Matter?

Open innovation and open-weight models made LocalLedger AI possible in ways proprietary closed APIs fundamentally cannot:

- **True Data Sovereignty:** In financial software, privacy is not a luxury—it is a legal and ethical mandate. Closed APIs require sending private invoices over public networks to third-party datacenters. Open-weight models like Qwen2.5 allow processing 100% on-device with zero data egress.
- **Zero Marginal Cost for Solo Operators:** Closed AI APIs bill per token. If a freelancer processes 300 receipts, a cloud API bill charges them for every page. With open-weight AI, after downloading the model once, the marginal cost per invoice is **$0.00**.
- **Offline Reliability:** Freelancers often work on trains, flights, or in cafes with unstable Wi-Fi. LocalLedger AI operates completely offline without internet dependencies or cloud API rate limits.
- **Hardware Democratization:** Thanks to open quantization (`Q4_K_M`), a capable 3.1-billion-parameter model runs comfortably on a standard developer laptop CPU with under 2 GB of RAM.

---

## My Agent Session

The entire project—from environment inspection and schema validation to SQLite persistence, Streamlit UI, duplicate prevention, and automated testing—was developed with an agentic pair programmer.

You can view the full architecture, test documentation, and development milestones directly in the repository:
- [Automated Testing Suite (36 Tests Passing)](https://github.com/snappyff43-hub/Ledger-AI/blob/main/TESTING.md)
- [Architecture & Sequence Diagrams](https://github.com/snappyff43-hub/Ledger-AI/blob/main/docs/ARCHITECTURE.md)
- [User Pilot Research Kit](https://github.com/snappyff43-hub/Ledger-AI/blob/main/CUSTOMER_PILOT.md)

---

## My First User

To ground the side hustle hypothesis in authentic feedback rather than assumptions, I prepared a comprehensive customer pilot kit:
- **Pilot Guide & Interview Script:** [`CUSTOMER_PILOT.md`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/CUSTOMER_PILOT.md)
- **Unpopulated Feedback Log:** [`PILOT_RESULTS_TEMPLATE.md`](https://github.com/snappyff43-hub/Ledger-AI/blob/main/PILOT_RESULTS_TEMPLATE.md)

The kit sets up a 5-minute live demonstration using synthetic test receipts, asking neutral questions about existing bookkeeping pain points, reaction to local-only privacy, acceptable processing latency on CPU (~30 seconds), and willingness to pay for a packaged desktop installer or white-glove setup.

---

## Prize Categories

- **Primary Track:** Side Hustle Challenge — Practical AI Tools for Independent Workers
- **Open-Source AI Track:** Projects built around open-weight models (Qwen2.5 3B via Ollama) with 100% on-device local inference.

---

*Built with ❤️ for freelancers who value their privacy and their time.*

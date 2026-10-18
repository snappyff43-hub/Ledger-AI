# Hackathon Submission Draft: LocalLedger AI

**Track / Category:** Side Hustle Challenge — Practical AI Tools for Independent Workers
**Project Name:** LocalLedger AI
**Repository State:** Local MVP Working Prototype (Python / Streamlit / Ollama / SQLite)

---

## 1. Product Overview & Problem Statement

Independent professionals, freelancers, and sole proprietors must track expenses for tax write-offs and client invoicing. However, the existing software landscape forces a difficult compromise:
1. **Cloud Privacy Risks:** Cloud-based receipt scanning apps send sensitive receipts, client names, hourly billing rates, and home addresses across public cloud APIs, risking confidential client information.
2. **Subscription Fatigue & Per-Token Costs:** Cloud AI services bill recurring monthly subscriptions or API fees per token, making automated receipt tracking prohibitively expensive for occasional expense tracking.
3. **Fragile Rule-Based Extractors:** Traditional regex tools break when invoices deviate from standard templates.

**LocalLedger AI** solves this by providing a zero-cloud, local-first invoice and receipt organizer. Powered by the open-weight **Qwen2.5 3B** model running entirely on the user's laptop via **Ollama**, it parses unstructured invoice documents into structured SQLite financial records with zero data egress and zero per-invoice API costs.

---

## 2. Intended Users & Value Proposition

- **Target Audience:** Freelancers, independent contractors, digital consultants, and micro-business operators.
- **Key Value Drivers:**
  - **100% On-Device Privacy:** Financial documents never leave the computer.
  - **Predictable Zero-Marginal-Cost:** Unlimited document processing without cloud API charges or monthly tiers.
  - **Human-in-the-Loop Safeguards:** Anti-hallucination prompts ensure missing fields remain `null`. Reviewers verify and adjust all fields before persistence.
  - **Portable Accounting Ready:** One-click CSV export with built-in spreadsheet formula injection protection.

---

## 3. Why Open-Weight AI & Local Inference Matter

Large Language Models excel at understanding unstructured documents, but financial data demands strict privacy. Open-weight models like **Qwen2.5 3B** represent a paradigm shift:
- **Efficiency on Commodity Hardware:** Quantized to 4-bit (`Q4_K_M`), Qwen2.5 3B requires under 2 GB of memory, making it practical to run on standard developer laptops without dedicated GPUs.
- **Deterministic Structured Output:** Leveraging Ollama's local JSON mode, the model extracts exact schemas without preamble text or markdown noise.
- **Freedom from Cloud Vendor Lock-In:** Independent workers are immune to cloud API rate limits, deprecations, or sudden price hikes.

---

## 4. Current Business Model Hypothesis

While the core LocalLedger AI code is designed as a free, open-weight tool, viable side-hustle commercialization pathways include:
1. **White-Glove Local Setup & Support:** A paid one-time service ($49–$99) assisting non-technical freelancers with local Ollama installation, model configuration, and migration of legacy CSV records.
2. **Custom Industry Category & Template Packs:** Pre-tuned prompt configurations and custom expense categories tailored for specific verticals (e.g., photographers, videographers, independent software contractors).
3. **Turnkey Packaged Binaries:** Creating one-click installers (e.g., PyInstaller / Electron wrapper) for macOS and Windows with bundled lightweight models.

---

## 5. Verified MVP Features & Live Test Results

All features below have been fully implemented and verified via automated and live integration testing:

- [x] **Live Local LLM Ingestion:** Tested with live `qwen2.5:3b` in Ollama; parsed synthetic invoices with dates, multi-item subtotals, taxes, and totals in ~27–35 seconds on CPU.
- [x] **Anti-Hallucination Integrity:** Tested sparse receipts lacking dates and invoice IDs; verified that the model returns `null` rather than fabricating missing details.
- [x] **Human Review & Error Warning:** Review form flags arithmetic discrepancies (`subtotal + tax != total`) and credit notes without modifying user data.
- [x] **Duplicate Protection:** Prevents duplicate saves by comparing `(vendor, invoice_number)` or `(vendor, date, total)`, requiring explicit override confirmation.
- [x] **Local Persistence & Export:** Stores confirmed records in SQLite (`data/ledger.db`); exports sanitized CSVs protected against spreadsheet formula injection (`=`, `@`, `+`, `-`).
- [x] **Comprehensive Test Suite:** 36 automated tests across document parsing, SQLite storage, canonical schema validation, CSV injection defense, benchmark skip safety, and boundary edge cases (100% passing).

---

## 6. Honest Limitations & Roadmap

- **Current Limitations:**
  - **Scanned Image PDFs:** Documents without an embedded text layer require manual text pasting, as local OCR (Tesseract) is not yet integrated.
  - **CPU Inference Speed:** On laptops lacking a dedicated NVIDIA GPU, extraction takes ~30 seconds per invoice.
- **Near-Term Roadmap:**
  - Local OCR fallback for scanned receipts and camera photos.
  - Optional multi-currency exchange rate conversion.
  - Export integrations with open-source accounting platforms (e.g., GnuCash, Ledger CLI).

---

## 7. Practical Plan for Initial User Feedback

To validate this side hustle concept with real users:
1. **Recruitment:** Reach out to 2–3 freelance developers or consultants within local co-working spaces or freelance forums.
2. **Hands-On Session (30 mins):** Walk them through extracting 3–5 of their own synthetic/sample receipts on their local machines.
3. **Evaluation Questions:**
   - *Did the local privacy guarantee increase your willingness to use AI for finance?*
   - *Was the 30-second CPU extraction delay acceptable compared to manual typing?*
   - *What custom categories or export formats are essential for your tax filing?*

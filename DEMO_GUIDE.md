# LocalLedger AI — Demonstration & Testing Guide

This guide provides a structured, rapid walkthrough to demonstrate LocalLedger AI during hackathon presentations, peer reviews, or user interviews.

---

## 60–90 Second Live Demo Script

| Time | Action | What to Say / Show |
| :--- | :--- | :--- |
| **0:00 - 0:15** | Open `http://localhost:8501`. Show the **Dashboard**. | *"Freelancers handle hundreds of sensitive receipts, but uploading them to cloud AI compromises privacy and racks up per-token API bills. LocalLedger AI is a 100% local-first invoice organizer running on open-weight models."* |
| **0:15 - 0:40** | Click **Add Invoice**, paste Synthetic Invoice A, and click **Extract Invoice Details**. | *"Here is an unformatted invoice text. With one click, our local Qwen2.5 3B model parses the vendor, invoice ID, date, tax, and currency without sending a single byte over the internet."* |
| **0:40 - 0:60** | Highlight the **Review Form** and click **Save Confirmed Invoice**. | *"LocalLedger AI never guesses or silently alters data. The user has full human-in-the-loop oversight to verify or adjust fields before saving to a local SQLite database."* |
| **0:60 - 0:75** | Paste Synthetic Invoice A again and click **Extract**, then **Save**. | *"Notice our duplicate detection: if you accidentally scan the same receipt twice, the system prevents duplicate entries and asks for explicit confirmation before saving."* |
| **0:75 - 0:90** | Switch to **Expense History**, filter by category, and click **Export Filtered Invoices (CSV)**. | *"You can search records, inspect category breakdowns, and export clean, sanitized CSVs directly into your accounting spreadsheet."* |

---

## Synthetic Test Documents

### Example A: Standard Invoice (Full Details)
Copy and paste this into the **Add Invoice** tab:

```text
========================================
Apex Studio Services LLC
404 Market Street, Suite 200, Austin, TX
Tax ID: 74-9876543

INVOICE
Invoice Number: APX-2026-901
Date: October 18, 2026
Due Date: November 18, 2026

Billed To:
Local Freelancer Co.
San Francisco, CA

ITEMS:
1. Cloud Server Hosting (Dedicated) - $120.00
2. Database Backup Storage (Monthly) - $20.00

Subtotal: $140.00
Tax (10%): $14.00
TOTAL: $154.00 USD

Payment terms: Net 30
Category: Software
Thank you for your business!
========================================
```

**Expected Extraction Outcome:**
- **Vendor:** `Apex Studio Services LLC`
- **Invoice Number:** `APX-2026-901`
- **Invoice Date:** `2026-10-18`
- **Subtotal:** `140.00`
- **Tax:** `14.00`
- **Total:** `154.00`
- **Currency:** `USD`
- **Category:** `Software`

---

### Example B: Sparse Receipt (Anti-Hallucination Demo)
Demonstrates that missing fields remain `null` / empty:

```text
City Transit Metro
Ticket #8812
Total: $5.50
Cash
```

**Expected Extraction Outcome:**
- **Vendor:** `City Transit Metro`
- **Invoice Number:** `8812` (or empty)
- **Invoice Date:** `null` / empty (not hallucinated)
- **Subtotal:** `5.50` (or `null`)
- **Tax:** `null` / empty (not hallucinated)
- **Total:** `5.50`
- **Currency:** `USD` (or empty)
- **Category:** `Travel` or `Other`

---

### Example C: Arithmetic Warning Demo
Demonstrates detection of math discrepancies:

```text
Vendor: Corner Hardware Store
Invoice #: HW-55
Subtotal: $50.00
Tax: $5.00
Total: $90.00 USD
```

**Expected Extraction Outcome:**
- The extraction preserves the numbers as printed on the invoice.
- A yellow warning alert is displayed:
  `⚠️ Arithmetic discrepancy detected: subtotal (50.0) + tax (5.0) = 55.0, which does not match total (90.0).`
- No automatic alterations are made to the user's data.

---

## Troubleshooting Guide

1. **Sidebar shows `○ Ollama Offline`:**
   - Verify Ollama is running in your Windows taskbar or open a terminal and run:
     ```powershell
     ollama serve
     ```
   - Confirm the API responds at `http://127.0.0.1:11434`.

2. **Model Not Found Error (`Model 'qwen2.5:3b' was not found`):**
   - In PowerShell, run:
     ```powershell
     ollama pull qwen2.5:3b
     ```
   - Refresh the Streamlit page.

3. **Inference is Taking 30+ Seconds:**
   - On CPU-only computers, open-weight language models run sequentially on CPU threads.
   - Close high-memory background browser tabs to prevent RAM paging.

---

## Demo Recording & Screenshot Checklist

- [ ] **Screenshot 1: Financial Dashboard** showing invoice count, primary currency spend, and the green `● Ollama Connected` badge.
- [ ] **Screenshot 2: Add Invoice Screen** showing extracted synthetic invoice fields neatly populated in the review form.
- [ ] **Screenshot 3: Duplicate Warning Dialog** demonstrating prevention of duplicate entries.
- [ ] **Screenshot 4: Expense History & Filter Table** with the **Export Filtered Invoices (CSV)** button.
- [ ] **Optional 60-Second Video / GIF:** Quick screen capture showing paste $\rightarrow$ extract $\rightarrow$ save $\rightarrow$ dashboard metric update.

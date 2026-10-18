# LocalLedger AI — Customer Pilot Guide

This document outlines a safe, practical framework for conducting a 1-on-1 feedback session with a freelancer or small-business owner. The goal is to evaluate the usability, privacy appeal, and commercial potential of LocalLedger AI using synthetic data.

---

## 1. Target Participant Profiles

Prioritize participants who regularly track business expenses or issue invoices:
- **Freelancers & Independent Contractors:** Software engineers, copywriters, graphic designers, video editors.
- **Independent Consultants & Tutors:** Educational tutors, coaches, business consultants.
- **Solo Micro-Business Owners:** Photography studio owners, freelance translators, independent tradespeople.

---

## 2. Five-Minute Demonstration Plan

Keep the demonstration structured, focused, and under 5 minutes so the participant has ample time to react and discuss:

| Step | Duration | Focus Area | Action & Talking Points |
| :--- | :--- | :--- | :--- |
| **1. The Problem** | 45 sec | Context | *"Managing expense receipts is tedious, but uploading sensitive client receipts to cloud AI apps risks privacy and racks up subscription costs."* |
| **2. Local Privacy** | 30 sec | Sidebar | Point to the green **● Ollama Connected** status: *"This entire tool runs 100% on this laptop using an open-weight 3B model. No data ever leaves the computer."* |
| **3. Live Extraction** | 60 sec | Add Invoice | Paste Synthetic Example A from `DEMO_GUIDE.md`. Click **Extract Invoice Details**. Show the model parsing vendor, invoice number, date, tax, and total. |
| **4. Human Review** | 45 sec | Review Form | Edit one field (e.g. adjust the category to *Software* or change the date) to demonstrate human-in-the-loop oversight. Click **Save Confirmed Invoice**. |
| **5. Search & Export** | 60 sec | History & CSV | Switch to **Expense History**. Search for the record, demonstrate the category filter, and click **Export Filtered Invoices (CSV)**. Show the clean spreadsheet download. |

---

## 3. Neutral Participant Interview Script

Ask neutral, open-ended questions to avoid leading the participant or soliciting polite, unhelpful agreement:

### Current Workflow & Pain Points
1. *“How do you currently organize your receipts and invoices for taxes or client billing?”*
2. *“Which specific part of that routine takes the most time or causes the most frustration?”*

### Product Fit & Value
3. *“Looking at what you just saw, does this tool address a problem you actually experience in your day-to-day work?”*
4. *“What would you need to see changed or improved before you would consider using it regularly?”*

### Privacy & Architecture
5. *“Does having the AI run entirely locally on your machine matter to you compared to a cloud service like ChatGPT or a web app?”*

### Willingness to Pay & Business Model
6. *“Would you consider paying for a tool like this? Why or why not?”*
7. *“If yes, what specific feature or service (e.g., custom setup, automated phone photo import, desktop app installer) would make it valuable enough to pay for?”*
8. *“What one feature should be added next?”*

---

## 4. Usability Scorecard

Use this checklist during or immediately after the demonstration to gauge real comprehension:

- [ ] **Extraction Comprehension:** Did the participant easily understand what the tool was doing when extracting fields?
- [ ] **Field Clarity:** Were the extracted labels (Vendor, Invoice #, Subtotal, Tax, Total, Currency, Category) intuitive to them?
- [ ] **Correction Usability:** Did they understand that they could edit or override any field before saving?
- [ ] **Trust in Local Processing:** Did the participant believe and value the local privacy explanation?
- [ ] **Export Utility:** Did they see immediate utility in the CSV export format for their accounting spreadsheets?
- [ ] **Friction / Hesitations:** Did the participant express concern over CPU processing time (~25–35s) or the command-line setup?

---

## 5. Privacy, Ethics & Participant Protection

- **Synthetic Data Only:** Always use the synthetic test documents from `DEMO_GUIDE.md` during the demo. Never ask the participant to supply real tax documents, bank statements, or confidential client receipts.
- **Consent:** If taking notes, audio recording, or recording the screen, request explicit verbal consent beforehand.
- **Anonymity:** Do not log or publish the participant's full name, email, business name, or physical address. Refer to them by general role (e.g., *“Independent UX Designer”* or *“Freelance Web Developer”*).
- **Objective Reporting:** Do not extrapolate a single participant's feedback into universal market proof. Record criticisms and hesitations with equal weight to positive feedback.

# LocalLedger AI — System Architecture & Workflow

This document details the architectural layout, core subsystems, data pipelines, and security boundaries implemented in **LocalLedger AI**.

---

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    classDef client fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0f172a;
    classDef localApp fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#0f172a;
    classDef storage fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#0f172a;
    classDef optionalCloud fill:#f1f5f9,stroke:#64748b,stroke-width:1px,stroke-dasharray: 5 5,color:#334155;

    subgraph UserInterface["User Presentation Layer"]
        UI["Streamlit Dashboard & Form (app.py)"]:::client
    end

    subgraph LocalProcessing["Local Core Processing (100% On-Device)"]
        Parser["Document Parser & Safety Guard (invoice_parser.py)"]:::localApp
        AIService["AI Service & Canonical Validator (ai_service.py)"]:::localApp
        Ollama["Local Ollama Service (http://127.0.0.1:11434)<br/>Model: qwen2.5:3b"]:::localApp
    end

    subgraph DataPersistence["Local Persistence & Output"]
        DB["SQLite Database (database.py -> data/ledger.db)"]:::storage
        CSV["Formula-Sanitized CSV Export"]:::storage
    end

    subgraph OptionalBench["Optional Benchmark Tool (Isolated)"]
        Bench["Model Benchmark Script (compare_models.py)"]:::optionalCloud
        Gemini["Optional Cloud Google Gemini<br/>(Requires explicit opt-in & API key)"]:::optionalCloud
    end

    UI -->|"Raw Pasted Text or PDF Bytes"| Parser
    Parser -->|"Sanitized Document Text"| AIService
    AIService -->|"REST API (JSON Format, Temp 0.0)"| Ollama
    Ollama -->|"Structured Invoice JSON"| AIService
    AIService -->|"Canonical Fields & Discrepancy Warnings"| UI
    UI -->|"Explicit User Confirmation"| DB
    DB -->|"Filtered Query Results"| UI
    DB -->|"Export Filtered Invoices"| CSV

    Bench -.->|"Synthetic Invoice Only"| AIService
    Bench -.->|"Optional Cloud API Call"| Gemini
```

---

## 2. Core Subsystems

### A. Presentation Layer (`app.py`)
- **Technology:** Streamlit.
- **Role:** Interactive dashboard, document ingestion forms, review and confirmation views, and tabular history exploration.
- **Human-in-the-Loop:** Displays AI-extracted fields in editable inputs. Requires the user to explicitly click **Save Confirmed Invoice** before committing data to disk.
- **Duplicate Interception:** If a record matches an existing invoice by `(vendor, invoice_number)` or `(vendor, date, total)`, displays an explicit warning modal requiring checkbox confirmation to prevent accidental re-saving.

### B. Document Parser & Pipeline Coordinator (`invoice_parser.py`)
- **Technology:** `pypdf` & Python standard library.
- **Safety Boundaries:** Enforces a 5 MB maximum file size and a 50,000 character length cap.
- **In-Memory Operation:** Uploaded PDF and TXT documents are parsed strictly in memory and are never saved to disk.
- **Scanned Document Detection:** Flags PDFs with 0 extractable text characters as scanned images, guiding the user to paste text manually rather than silently failing.

### C. AI Inference & Canonical Validator (`ai_service.py`)
- **Technology:** Local Ollama REST API (`/api/generate` with `format: "json"`).
- **Default Model:** `qwen2.5:3b` (3.1B parameter open-weight model).
- **Anti-Hallucination Design:** Prompt instructions strictly forbid guessing missing values. Missing fields evaluate to `null` / `None`.
- **Validation Engine:** Normalizes dates into ISO `YYYY-MM-DD`, accepts legitimate `0.0` values, flags negative credit notes, and detects arithmetic discrepancies (`subtotal + tax != total`) without mutating original values.

### D. Persistence & CSV Exporter (`database.py`)
- **Technology:** Python built-in `sqlite3`.
- **Database Path:** `data/ledger.db` (auto-created and indexed on startup).
- **Data Privacy:** Raw document text and PDF binary streams are never persisted. Only confirmed canonical fields, source filenames, and ISO timestamps are stored.
- **CSV Formula Injection Mitigation:** All untrusted text fields exported to CSV are checked; leading formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with a leading apostrophe.

### E. Optional Benchmark Tool (`compare_models.py`)
- **Completely Decoupled:** Exists solely for developer benchmarking on fixed synthetic data (`ACME CLOUD SOLUTIONS LLC`).
- **Safe Skip Logic:** If `GEMINI_API_KEY` is not present, the script executes Ollama and skips Gemini without crashing or exposing secrets.

---

## 3. Invoice Processing Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Freelancer / User
    participant UI as Streamlit UI (app.py)
    participant Parser as Parser (invoice_parser.py)
    participant AI as AI Service (ai_service.py)
    participant Ollama as Local Ollama (qwen2.5:3b)
    participant DB as SQLite (database.py)

    User->>UI: Pastes text or uploads PDF/TXT
    User->>UI: Clicks "Extract Invoice Details"
    UI->>Parser: process_invoice_document(input_source)
    Parser->>Parser: Enforce 5 MB limit & extract in-memory text
    Parser->>AI: extract_invoice_data(invoice_text)
    AI->>Ollama: POST /api/generate (JSON mode, temp 0.0)
    Ollama-->>AI: Raw JSON response string
    AI->>AI: parse_and_validate_extraction()
    AI-->>Parser: Cleaned canonical fields & warnings
    Parser-->>UI: Fields & arithmetic check results
    UI->>User: Displays editable review form
    User->>UI: Reviews, corrects fields, clicks "Save"
    UI->>DB: check_for_duplicates(record)
    alt Duplicate Found
        DB-->>UI: Matches detected
        UI->>User: Shows duplicate warning dialog
    else No Duplicate / User Confirmed
        UI->>DB: save_invoice(record)
        DB-->>UI: Inserted Record ID
        UI->>User: "Invoice successfully saved!"
    end
```

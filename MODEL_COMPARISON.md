# LocalLedger AI — Model Benchmark & Comparison Guide

This document describes the optional evaluation tool `compare_models.py`, which compares on-device inference using **Ollama (Qwen2.5 3B)** against optional cloud-hosted inference using **Google Gemini** on a fixed, synthetic invoice.

---

## 1. Architectural Philosophy & Privacy Stance

- **Primary & Default Engine:** LocalLedger AI is built exclusively for local-first, zero-cloud operation. In everyday use, all invoice extraction is processed locally by Ollama (`http://127.0.0.1:11434`).
- **Benchmark Isolation:** The benchmark script (`compare_models.py`) is completely decoupled from the core application (`app.py`, `database.py`, `invoice_parser.py`).
- **Synthetic Data Only:** The benchmark evaluates only a fixed synthetic invoice document (`ACME CLOUD SOLUTIONS LLC`). Real receipts, customer details, and database records are **never** transmitted externally.

---

## 2. Security & Environment Configuration

### Protecting Your API Key
1. **Never Hardcode Secrets:** The benchmark script reads the Gemini API key exclusively from the `GEMINI_API_KEY` environment variable.
2. **Revocation Notice:** Any API key accidentally exposed in console logs or shared chats should be revoked immediately in the [Google AI Studio console](https://aistudio.google.com/).
3. **Setting the Variable in Windows PowerShell:**
   Ensure you wrap the key in quotes:
   ```powershell
   $env:GEMINI_API_KEY="your_api_key_here"
   ```
4. **Configuring the Model Identifier (Optional):**
   ```powershell
   $env:GEMINI_MODEL="gemini-2.5-flash"
   ```
   *(Defaults to `gemini-3.8-flash` if unspecified).*

---

## 3. How to Run the Benchmark

### Mode A: Local Ollama Only (No Cloud Key Required)
If `GEMINI_API_KEY` is not set or the optional `google-genai` SDK is not installed, the tool evaluates local Ollama and skips Gemini:

```powershell
cd E:\Hacktoberweek2\localledger_ai
$env:PYTHONPATH="E:\Hacktoberweek2\localledger_ai"
.\.venv\Scripts\python.exe compare_models.py
```

### Mode B: Dual Comparison (Ollama vs. Gemini)
1. Install the optional dependency from `requirements-gemini.txt`:
   ```powershell
   .\.venv\Scripts\pip.exe install -r requirements-gemini.txt
   ```
2. Set the environment variable securely:
   ```powershell
   $env:GEMINI_API_KEY="your_actual_key"
   ```
3. Run the comparison:
   ```powershell
   .\.venv\Scripts\python.exe compare_models.py
   ```

---

## 4. Understanding Benchmark Metrics & Trade-offs

| Dimension | Local Ollama (Qwen2.5 3B) | Cloud Gemini (e.g., Flash) |
| :--- | :--- | :--- |
| **Data Privacy** | **100% On-Device:** Financial records never leave localhost. | **Third-Party Transmission:** Document text is sent over HTTPS to cloud servers. |
| **Recurring Cost** | **$0.00:** Free, unlimited open-weight execution. | **Pay-Per-Token:** Billed per request / token after free tiers. |
| **Offline Capability** | **Full:** Operates without an active internet connection. | **None:** Fails when offline or when API endpoints degrade. |
| **Inference Speed** | **Hardware Dependent:** ~25–55 seconds on consumer CPU. | **Fast:** Typically 1–3 seconds via cloud datacenter accelerators. |
| **Field Accuracy** | **High on Standard Invoices:** Achieves 100% agreement on standard canonical fields with JSON schema enforcement. | **High:** Strong performance across multilingual and complex tabular documents. |

---

## 5. Factors Influencing Performance Variations

1. **CPU vs. GPU:** Local execution speed depends directly on hardware. Systems with dedicated GPUs (via CUDA/ROCm) can achieve 2–5s inference with Ollama, whereas CPU execution takes longer.
2. **Network Jitter:** Cloud model latency includes DNS resolution, TLS handshakes, and transit latency.
3. **Quantization:** Local models utilize 4-bit quantization (`Q4_K_M`) to minimize memory footprint (< 2 GB RAM).

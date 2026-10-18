"""
app.py - Streamlit User Interface for LocalLedger AI.
Local-first invoice & receipt organizer for freelancers and small businesses.
Uses local Ollama AI for extraction, SQLite for local storage, and safe CSV export.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

# Import backend modules
from ai_service import (
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    check_ollama_status,
    get_available_models,
    validate_and_clean_invoice_data,
)
from database import (
    check_for_duplicates,
    export_invoices_to_csv,
    get_expense_summary,
    list_invoices,
    save_invoice,
    search_and_filter_invoices,
)
from invoice_parser import process_invoice_document

# Standard category choices for dropdown
STANDARD_CATEGORIES = [
    "Software",
    "Meals & Entertainment",
    "Office Supplies",
    "Travel",
    "Utilities",
    "Consulting",
    "Hardware",
    "Legal & Accounting",
    "Advertising",
    "Other",
]

# Page configuration
st.set_page_config(
    page_title="LocalLedger AI",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom minimalist finance styling (light, restrained blue accent, readable typography)
st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.6rem;
        color: #0f172a;
        font-weight: 700;
        margin-top: 4px;
    }
    .status-badge-ok {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        background-color: #ecfdf5;
        color: #047857;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .status-badge-warn {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        background-color: #fffbeb;
        color: #b45309;
        font-size: 0.82rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize persistent Streamlit session keys."""
    if "pending_invoice" not in st.session_state:
        st.session_state.pending_invoice = None
    if "pending_raw_text" not in st.session_state:
        st.session_state.pending_raw_text = ""
    if "pending_source_filename" not in st.session_state:
        st.session_state.pending_source_filename = None
    if "pending_warnings" not in st.session_state:
        st.session_state.pending_warnings = []
    if "save_confirmed_duplicate" not in st.session_state:
        st.session_state.save_confirmed_duplicate = False


def reset_pending_invoice():
    """Clear in-memory pending invoice state."""
    st.session_state.pending_invoice = None
    st.session_state.pending_raw_text = ""
    st.session_state.pending_source_filename = None
    st.session_state.pending_warnings = []
    st.session_state.save_confirmed_duplicate = False


def render_sidebar() -> Tuple[str, str, str]:
    """Renders sidebar navigation and local Ollama connection controls."""
    with st.sidebar:
        st.title("📑 LocalLedger AI")
        st.caption("Local-first freelance invoice organizer")
        st.divider()

        nav_choice = st.radio(
            "Navigation",
            ["Dashboard", "Add Invoice", "Expense History"],
            label_visibility="collapsed",
        )

        st.divider()
        st.subheader("Local AI Settings")

        base_url = st.text_input(
            "Ollama Base URL",
            value=DEFAULT_OLLAMA_URL,
            help="Local REST endpoint for Ollama.",
        )

        # Check Ollama connectivity
        is_alive, status_msg = check_ollama_status(base_url)

        if is_alive:
            st.markdown('<span class="status-badge-ok">● Ollama Connected</span>', unsafe_allow_html=True)
            available_models = get_available_models(base_url)
            if available_models:
                selected_model = st.selectbox(
                    "Model",
                    available_models,
                    index=available_models.index(DEFAULT_MODEL) if DEFAULT_MODEL in available_models else 0,
                )
            else:
                st.warning("No models found in Ollama. Pull a model using `ollama pull qwen2.5:3b`.")
                selected_model = DEFAULT_MODEL
        else:
            st.markdown('<span class="status-badge-warn">○ Ollama Offline</span>', unsafe_allow_html=True)
            st.caption(f"Status: {status_msg}")
            st.info("💡 To use AI extraction, start Ollama locally (`ollama run qwen2.5:3b`).")
            selected_model = DEFAULT_MODEL

        st.divider()
        st.caption("🔒 **Privacy Guarantee**: 100% local by default. Invoices and data never leave this machine. Cloud model evaluation via `compare_models.py` is strictly optional and isolated.")

        return nav_choice, base_url, selected_model


# -----------------------------------------------------------------------------
# SCREEN 1: DASHBOARD
# -----------------------------------------------------------------------------
def render_dashboard(is_alive: bool, selected_model: str):
    st.header("Financial Dashboard")
    st.write("Summary of all confirmed expenses stored in your local SQLite ledger.")

    summary, err = get_expense_summary()
    if err:
        st.error(f"Could not load ledger statistics: {err}")
        return

    total_invoices = summary.get("total_invoices", 0)

    # Empty state
    if total_invoices == 0:
        st.info("📭 Your local ledger is currently empty. Use the **Add Invoice** tab to scan your first receipt or invoice.")
        st.divider()
        st.subheader("System Status")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Ollama Service", "Connected" if is_alive else "Offline")
        with col_s2:
            st.metric("Extraction Model", selected_model)
        return

    # Metrics Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Confirmed Invoices</div>
                <div class="metric-value">{total_invoices}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        by_currency = summary.get("by_currency", [])
        if by_currency:
            primary_curr = by_currency[0]
            display_total = f"{primary_curr['currency']} {primary_curr['total']:,.2f}"
            subtitle = f"Across {primary_curr['count']} invoice(s)"
        else:
            display_total = "0.00"
            subtitle = "No totals recorded"

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Primary Spend ({by_currency[0]['currency'] if by_currency else 'N/A'})</div>
                <div class="metric-value">{display_total}</div>
                <small style="color:#64748b;">{subtitle}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Local AI Engine</div>
                <div class="metric-value" style="font-size:1.2rem; padding-top:6px;">
                    {'🟢 Ready' if is_alive else '🟠 Offline'}
                </div>
                <small style="color:#64748b;">Model: {selected_model}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Multi-currency display if more than one currency is present
    if len(by_currency) > 1:
        st.subheader("Totals by Currency")
        curr_cols = st.columns(min(len(by_currency), 4))
        for idx, c_item in enumerate(by_currency):
            with curr_cols[idx % len(curr_cols)]:
                st.metric(
                    label=f"Currency: {c_item['currency']}",
                    value=f"{c_item['total']:,.2f}",
                    delta=f"{c_item['count']} invoice(s)",
                )

    st.divider()

    # Category Breakdown & Recent Invoices
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Expenses by Category")
        by_category = summary.get("by_category", [])
        if by_category:
            # Format as clean table
            cat_data = [
                {"Category": item["category"], "Invoices": item["count"], "Total": f"{item['total']:,.2f}"}
                for item in by_category
            ]
            st.dataframe(cat_data, use_container_width=True, hide_index=True)
        else:
            st.caption("No categorized expenses available.")

    with right_col:
        st.subheader("Recent Invoices")
        recent, r_err = list_invoices(limit=5)
        if recent:
            recent_table = [
                {
                    "Vendor": r.get("vendor") or "Unknown",
                    "Date": r.get("invoice_date") or "-",
                    "Total": f"{r.get('currency') or ''} {r.get('total') or 0.0:,.2f}",
                    "Category": r.get("category") or "Uncategorized",
                }
                for r in recent
            ]
            st.dataframe(recent_table, use_container_width=True, hide_index=True)
        else:
            st.caption("No recent records found.")


# -----------------------------------------------------------------------------
# SCREEN 2: ADD INVOICE
# -----------------------------------------------------------------------------
def render_add_invoice(base_url: str, selected_model: str, is_alive: bool):
    st.header("Add & Review Invoice")
    st.write("Upload a PDF/TXT invoice or paste document text. Extract fields locally, review, and confirm.")

    # 1. Document Input Section
    input_method = st.radio("Choose input method:", ["Upload File (PDF / TXT)", "Paste Invoice Text"], horizontal=True)

    uploaded_file = None
    pasted_text = ""

    if input_method == "Upload File (PDF / TXT)":
        uploaded_file = st.file_uploader(
            "Upload invoice or receipt (Max 5 MB)",
            type=["pdf", "txt"],
            help="Text-based PDFs and TXT files only. Scanned images without text cannot be parsed without OCR.",
        )
    else:
        pasted_text = st.text_area(
            "Paste invoice or receipt text below:",
            height=180,
            placeholder="e.g.\nVendor: FastCloud Hosting\nInvoice: INV-2024-001\nDate: 2024-10-15\nSubtotal: $100.00\nTax: $15.00\nTotal: $115.00 USD",
        )

    # 2. Extract Action
    extract_col1, extract_col2 = st.columns([1, 4])
    with extract_col1:
        extract_button = st.button("🔍 Extract Invoice Details", type="primary", use_container_width=True)

    if extract_button:
        if not is_alive:
            st.error(
                "❌ **Ollama is offline or unreachable.**\n\n"
                "LocalLedger AI requires Ollama running locally to extract invoice fields.\n\n"
                "**Setup steps:**\n"
                "1. Open a terminal and run `ollama run qwen2.5:3b`\n"
                "2. Refresh this page or check the connection status in the sidebar."
            )
            return

        has_input = (uploaded_file is not None) or (pasted_text.strip() != "")
        if not has_input:
            st.warning("⚠️ Please provide invoice text by pasting or uploading a file.")
            return

        with st.spinner("Analyzing document with local Qwen2.5 model..."):
            source_content = uploaded_file.getvalue() if uploaded_file else pasted_text
            filename = uploaded_file.name if uploaded_file else None

            success, raw_text, fields, warnings, err = process_invoice_document(
                input_source=source_content,
                filename=filename,
                base_url=base_url,
                model=selected_model,
            )

            if not success:
                st.error(f"Extraction failed: {err}")
                if raw_text:
                    st.session_state.pending_raw_text = raw_text
                    st.info("The raw document text was preserved. You can review it or enter fields manually.")
            else:
                st.session_state.pending_invoice = fields
                st.session_state.pending_raw_text = raw_text
                st.session_state.pending_source_filename = filename
                st.session_state.pending_warnings = warnings
                st.session_state.save_confirmed_duplicate = False
                st.success("✅ Extraction complete! Please review and confirm the fields below.")

    st.divider()

    # 3. Editable Review Form
    if st.session_state.pending_invoice is not None:
        st.subheader("Review Extracted Fields")
        st.caption("Verify and correct any missing or uncertain fields. No data is stored until you click **Save Confirmed Invoice**.")

        # Show extraction warnings if any
        if st.session_state.pending_warnings:
            for w in st.session_state.pending_warnings:
                st.warning(f"⚠️ {w}")

        current_data = st.session_state.pending_invoice

        with st.form("invoice_review_form"):
            c1, c2 = st.columns(2)
            with c1:
                vendor_val = st.text_input("Vendor / Company Name", value=current_data.get("vendor") or "")
                inv_num_val = st.text_input("Invoice Number", value=current_data.get("invoice_number") or "")

                # Invoice date handling
                date_str = current_data.get("invoice_date") or ""
                inv_date_val = st.text_input("Invoice Date (YYYY-MM-DD)", value=date_str, help="Format: YYYY-MM-DD")

                currency_val = st.text_input("Currency", value=current_data.get("currency") or "USD")

            with c2:
                # Monetary values
                subtotal_val = st.number_input(
                    "Subtotal",
                    value=float(current_data["subtotal"]) if current_data.get("subtotal") is not None else 0.0,
                    step=0.01,
                    format="%.2f",
                )
                tax_val = st.number_input(
                    "Tax Amount",
                    value=float(current_data["tax"]) if current_data.get("tax") is not None else 0.0,
                    step=0.01,
                    format="%.2f",
                )
                total_val = st.number_input(
                    "Total Amount",
                    value=float(current_data["total"]) if current_data.get("total") is not None else 0.0,
                    step=0.01,
                    format="%.2f",
                )

                # Category selector
                cat_current = current_data.get("category") or "Other"
                cat_idx = STANDARD_CATEGORIES.index(cat_current) if cat_current in STANDARD_CATEGORIES else len(STANDARD_CATEGORIES) - 1
                category_val = st.selectbox("Expense Category", STANDARD_CATEGORIES, index=cat_idx)

            with st.expander("📄 View Extracted Raw Document Text"):
                st.text(st.session_state.pending_raw_text or "No raw text available.")

            btn_col1, btn_col2, _ = st.columns([2, 1, 3])
            with btn_col1:
                save_submitted = st.form_submit_button("💾 Save Confirmed Invoice", type="primary", use_container_width=True)
            with btn_col2:
                cancel_submitted = st.form_submit_button("Cancel", use_container_width=True)

        if cancel_submitted:
            reset_pending_invoice()
            st.rerun()

        if save_submitted:
            # Package verified form fields
            confirmed_data = {
                "vendor": vendor_val.strip() or None,
                "invoice_number": inv_num_val.strip() or None,
                "invoice_date": inv_date_val.strip() or None,
                "subtotal": subtotal_val if subtotal_val != 0.0 or current_data.get("subtotal") == 0.0 else None,
                "tax": tax_val if tax_val != 0.0 or current_data.get("tax") == 0.0 else None,
                "total": total_val,
                "currency": currency_val.strip().upper() or "USD",
                "category": category_val,
            }

            # Canonical validation
            clean_record, revalidation_warnings = validate_and_clean_invoice_data(confirmed_data)

            # Check for duplicates unless user explicitly confirmed saving duplicate
            has_dup, matches, dup_err = check_for_duplicates(clean_record)
            if has_dup and not st.session_state.save_confirmed_duplicate:
                st.warning("⚠️ **Potential Duplicate Detected!** An invoice with matching details already exists:")
                for m in matches:
                    st.write(
                        f"• **ID {m['id']}**: {m.get('vendor')} | #{m.get('invoice_number')} | Date: {m.get('invoice_date')} | Total: {m.get('currency')} {m.get('total')}"
                    )
                st.info("To save this record anyway without overwriting, click the checkbox below and press Save again.")
                st.session_state.save_confirmed_duplicate = st.checkbox("Confirm: Save anyway as a new record")
            else:
                ok, rec_id, db_err = save_invoice(
                    invoice_data=clean_record,
                    source_filename=st.session_state.pending_source_filename,
                )
                if ok:
                    st.success(f"🎉 Invoice successfully saved! (Record ID #{rec_id})")
                    reset_pending_invoice()
                    st.rerun()
                else:
                    st.error(f"Failed to save invoice to SQLite: {db_err}")


# -----------------------------------------------------------------------------
# SCREEN 3: EXPENSE HISTORY
# -----------------------------------------------------------------------------
def render_expense_history():
    st.header("Expense History & Export")
    st.write("Search, filter, review, and export confirmed invoice records to CSV.")

    # Filter controls
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
    with f_col1:
        search_query = st.text_input("Search Vendor or Invoice #", placeholder="e.g. Acme or INV-100")
    with f_col2:
        cat_filter = st.selectbox("Category", ["All"] + STANDARD_CATEGORIES)
    with f_col3:
        d_from = st.date_input("From Date", value=None)
    with f_col4:
        d_to = st.date_input("To Date", value=None)

    date_from_str = d_from.strftime("%Y-%m-%d") if d_from else None
    date_to_str = d_to.strftime("%Y-%m-%d") if d_to else None

    # Query SQLite database
    records, err = search_and_filter_invoices(
        search_query=search_query,
        category=cat_filter if cat_filter != "All" else None,
        date_from=date_from_str,
        date_to=date_to_str,
    )

    if err:
        st.error(f"Error querying database: {err}")
        return

    st.caption(f"Showing **{len(records)}** matching record(s)")

    if not records:
        st.info("No records matched your search/filter criteria.")
        return

    # Display Table
    table_data = []
    for r in records:
        table_data.append({
            "ID": r["id"],
            "Vendor": r.get("vendor") or "Unknown",
            "Invoice #": r.get("invoice_number") or "-",
            "Date": r.get("invoice_date") or "-",
            "Subtotal": f"{r.get('subtotal'):,.2f}" if r.get("subtotal") is not None else "-",
            "Tax": f"{r.get('tax'):,.2f}" if r.get("tax") is not None else "-",
            "Total": f"{r.get('total'):,.2f}" if r.get("total") is not None else "0.00",
            "Currency": r.get("currency") or "USD",
            "Category": r.get("category") or "Uncategorized",
            "Source File": r.get("source_filename") or "-",
        })

    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Export Action
    st.divider()
    exp_col1, _ = st.columns([2, 4])
    with exp_col1:
        ok, csv_data, exp_err = export_invoices_to_csv(records)
        if ok:
            export_filename = f"localledger_export_{date.today().strftime('%Y%m%d')}.csv"
            st.download_button(
                label="📥 Export Filtered Invoices (CSV)",
                data=csv_data.encode("utf-8"),
                file_name=export_filename,
                mime="text/csv",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.error(f"Failed to generate CSV: {exp_err}")


# -----------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -----------------------------------------------------------------------------
def main():
    init_session_state()
    nav_choice, base_url, selected_model = render_sidebar()

    is_alive, _ = check_ollama_status(base_url)

    if nav_choice == "Dashboard":
        render_dashboard(is_alive, selected_model)
    elif nav_choice == "Add Invoice":
        render_add_invoice(base_url, selected_model, is_alive)
    elif nav_choice == "Expense History":
        render_expense_history()


if __name__ == "__main__":
    main()

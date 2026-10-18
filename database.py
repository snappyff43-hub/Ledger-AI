"""
database.py - Local SQLite database storage and safe CSV export for LocalLedger AI.
Handles persistence, schema initialization, duplicate detection, searching,
filtering, expense aggregations, and formula-injection-safe CSV export.
"""

import csv
import io
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default storage location: project_dir/data/ledger.db
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "ledger.db")

# Canonical fields matching ai_service.py schema
CANONICAL_INVOICE_FIELDS = [
    "vendor",
    "invoice_number",
    "invoice_date",
    "subtotal",
    "tax",
    "total",
    "currency",
    "category",
]

CSV_EXPORT_COLUMNS = [
    ("id", "ID"),
    ("vendor", "Vendor"),
    ("invoice_number", "Invoice Number"),
    ("invoice_date", "Date"),
    ("subtotal", "Subtotal"),
    ("tax", "Tax"),
    ("total", "Total"),
    ("currency", "Currency"),
    ("category", "Category"),
    ("source_filename", "Source File"),
    ("created_at", "Recorded At"),
]


def sanitize_csv_cell(value: Any) -> str:
    """
    Sanitize text to prevent spreadsheet formula injection (CSV Injection).
    Prepends an apostrophe if text begins with =, +, -, @, or tab/CR.
    Preserves None as empty string and floats/ints as clean numbers.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)

    str_val = str(value)
    # Strip leading whitespace before checking for formula prefix
    stripped = str_val.lstrip()
    if stripped and stripped[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{str_val}"
    return str_val


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Open connection to SQLite database. Ensures parent directory exists.
    Enforces row_factory = sqlite3.Row for dictionary-like column access.
    """
    parent_dir = os.path.dirname(os.path.abspath(db_path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, Optional[str]]:
    """
    Initializes the SQLite schema if it does not already exist.
    Creates table 'invoices' and supporting indices.
    Returns: (success: bool, error_message: Optional[str])
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor TEXT,
                    invoice_number TEXT,
                    invoice_date TEXT,
                    subtotal REAL,
                    tax REAL,
                    total REAL,
                    currency TEXT,
                    category TEXT,
                    source_filename TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            # Create indices for fast lookup and search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_category ON invoices(category)")
            conn.commit()
            return True, None
    except Exception as exc:
        logger.error("Failed to initialize database at %s: %s", db_path, exc)
        return False, f"Database initialization failed: {str(exc)}"


def check_for_duplicates(
    invoice_data: Dict[str, Any],
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
    """
    Detect likely duplicate invoices based on vendor, invoice_number, and invoice_date.
    Does NOT assume invoice numbers are globally unique across all vendors.
    Returns: (has_duplicates: bool, matches: List[Dict], error: Optional[str])
    """
    vendor = invoice_data.get("vendor")
    inv_num = invoice_data.get("invoice_number")
    inv_date = invoice_data.get("invoice_date")

    # If there are not enough distinguishing fields, we cannot reliably flag duplicates
    if not vendor and not inv_num:
        return False, [], None

    try:
        init_db(db_path)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            # Match 1: Vendor and invoice_number match (strongest signal)
            if vendor and inv_num:
                cursor.execute(
                    "SELECT * FROM invoices WHERE LOWER(vendor) = LOWER(?) AND LOWER(invoice_number) = LOWER(?)",
                    (str(vendor).strip(), str(inv_num).strip()),
                )
            # Match 2: Vendor and date match with same total if invoice_number is absent
            elif vendor and inv_date and invoice_data.get("total") is not None:
                cursor.execute(
                    "SELECT * FROM invoices WHERE LOWER(vendor) = LOWER(?) AND invoice_date = ? AND ABS(total - ?) < 0.01",
                    (str(vendor).strip(), str(inv_date).strip(), float(invoice_data["total"])),
                )
            else:
                return False, [], None

            rows = cursor.fetchall()
            matches = [dict(row) for row in rows]
            return len(matches) > 0, matches, None
    except Exception as exc:
        return False, [], f"Error checking for duplicates: {str(exc)}"


def save_invoice(
    invoice_data: Dict[str, Any],
    source_filename: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Saves a user-confirmed invoice record into the local SQLite database.
    Generates an ISO timestamp for created_at.
    Returns: (success: bool, record_id: Optional[int], error_message: Optional[str])
    """
    try:
        init_db(db_path)
        created_at = datetime.now().isoformat()
        clean_filename = os.path.basename(source_filename) if source_filename else None

        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoices (
                    vendor, invoice_number, invoice_date,
                    subtotal, tax, total,
                    currency, category,
                    source_filename, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_data.get("vendor"),
                    invoice_data.get("invoice_number"),
                    invoice_data.get("invoice_date"),
                    invoice_data.get("subtotal"),
                    invoice_data.get("tax"),
                    invoice_data.get("total"),
                    invoice_data.get("currency"),
                    invoice_data.get("category"),
                    clean_filename,
                    created_at,
                ),
            )
            conn.commit()
            inserted_id = cursor.lastrowid
            return True, inserted_id, None
    except Exception as exc:
        logger.error("Failed to save invoice: %s", exc)
        return False, None, f"Failed to save invoice record: {str(exc)}"


def get_invoice_by_id(
    record_id: int,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Retrieves a single invoice record by its primary key ID.
    Returns: (record_dict or None, error_message or None)
    """
    try:
        init_db(db_path)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if row:
                return dict(row), None
            return None, f"Invoice with ID {record_id} not found."
    except Exception as exc:
        return None, f"Database error: {str(exc)}"


def list_invoices(
    limit: int = 500,
    offset: int = 0,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Lists saved invoices ordered newest first (by id DESC).
    Returns: (records_list, error_message or None)
    """
    try:
        init_db(db_path)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
            rows = cursor.fetchall()
            return [dict(r) for r in rows], None
    except Exception as exc:
        return [], f"Database error: {str(exc)}"


def search_and_filter_invoices(
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Search and filter invoices using parameterized queries.
    - search_query matches vendor or invoice_number.
    - category filters by exact category name.
    - date_from / date_to filters invoice_date range.
    Returns: (records_list, error_message or None)
    """
    try:
        init_db(db_path)
        conditions = []
        params: List[Any] = []

        if search_query and search_query.strip():
            q = f"%{search_query.strip()}%"
            conditions.append("(vendor LIKE ? OR invoice_number LIKE ?)")
            params.extend([q, q])

        if category and category.strip() and category.strip().lower() != "all":
            conditions.append("category = ?")
            params.append(category.strip())

        if date_from and date_from.strip():
            conditions.append("invoice_date >= ?")
            params.append(date_from.strip())

        if date_to and date_to.strip():
            conditions.append("invoice_date <= ?")
            params.append(date_to.strip())

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query_sql = f"SELECT * FROM invoices{where_clause} ORDER BY id DESC"

        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows], None
    except Exception as exc:
        return [], f"Database search failed: {str(exc)}"


def get_expense_summary(
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Computes overall counts and expense aggregations:
    - total_invoices: int
    - total_spent: float
    - by_category: List[Dict[str, Any]] (category, count, sum_total)
    - by_currency: List[Dict[str, Any]] (currency, count, sum_total)
    Returns: (summary_dict, error_message or None)
    """
    try:
        init_db(db_path)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()

            # Overall count and sum
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0.0) FROM invoices")
            total_count, total_spent = cursor.fetchone()

            # By category
            cursor.execute("""
                SELECT COALESCE(category, 'Uncategorized') AS cat,
                       COUNT(*) AS count,
                       COALESCE(SUM(total), 0.0) AS total_sum
                FROM invoices
                GROUP BY cat
                ORDER BY total_sum DESC
            """)
            by_category = [{"category": row[0], "count": row[1], "total": round(row[2], 2)} for row in cursor.fetchall()]

            # By currency
            cursor.execute("""
                SELECT COALESCE(currency, 'Unknown') AS curr,
                       COUNT(*) AS count,
                       COALESCE(SUM(total), 0.0) AS total_sum
                FROM invoices
                GROUP BY curr
                ORDER BY total_sum DESC
            """)
            by_currency = [{"currency": row[0], "count": row[1], "total": round(row[2], 2)} for row in cursor.fetchall()]

            summary = {
                "total_invoices": total_count,
                "total_spent": round(total_spent, 2),
                "by_category": by_category,
                "by_currency": by_currency,
            }
            return summary, None
    except Exception as exc:
        return {}, f"Failed to compute expense summary: {str(exc)}"


def export_invoices_to_csv(
    invoices: List[Dict[str, Any]],
) -> Tuple[bool, str, Optional[str]]:
    """
    Exports a list of invoice records to an in-memory CSV string.
    Applies formula-injection sanitization to untrusted text cells.
    Preserves Unicode, commas, quotes, and numeric amounts.
    Returns: (success: bool, csv_string: str, error_message: Optional[str])
    """
    if not isinstance(invoices, list):
        return False, "", "Invoices data must be a list of records."

    try:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Write header
        headers = [col[1] for col in CSV_EXPORT_COLUMNS]
        writer.writerow(headers)

        # Write rows
        for record in invoices:
            row = []
            for field_key, _ in CSV_EXPORT_COLUMNS:
                val = record.get(field_key)
                sanitized_val = sanitize_csv_cell(val)
                row.append(sanitized_val)
            writer.writerow(row)

        return True, output.getvalue(), None
    except Exception as exc:
        return False, "", f"CSV export failed: {str(exc)}"

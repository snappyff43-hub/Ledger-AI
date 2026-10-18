"""
invoice_parser.py - Safe text extraction and AI pipeline integration for LocalLedger AI.
Extracts text from pasted content, uploaded TXT files, and text-based PDF documents (via pypdf).
Coordinates pipeline between raw document text and ai_service without persistent storage.
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ai_service import (
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    extract_invoice_data,
    validate_and_clean_invoice_data,
)

logger = logging.getLogger(__name__)

# Safety constraints
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_TEXT_CHAR_LIMIT = 50_000  # Cap extracted text length to avoid memory/context bloat
ALLOWED_EXTENSIONS = {".txt", ".pdf"}


def validate_pasted_text(text: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates and sanitizes user-pasted invoice text.
    Returns: (is_valid: bool, cleaned_text: str, error_message: Optional[str])
    """
    if not text or not isinstance(text, str):
        return False, "", "Pasted text is empty."

    cleaned = text.strip()
    if not cleaned:
        return False, "", "Pasted text contains only whitespace."

    if len(cleaned) > MAX_TEXT_CHAR_LIMIT:
        cleaned = cleaned[:MAX_TEXT_CHAR_LIMIT]
        logger.warning("Pasted text exceeded %d characters; truncated.", MAX_TEXT_CHAR_LIMIT)

    return True, cleaned, None


def extract_text_from_txt(file_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Extracts text from uploaded TXT file bytes with robust character encoding fallbacks.
    Returns: (is_valid: bool, extracted_text: str, error_message: Optional[str])
    """
    if not file_bytes:
        return False, "", "TXT file is empty (0 bytes)."

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, "", f"File size ({len(file_bytes)} bytes) exceeds maximum allowed limit of 5 MB."

    # Try common encodings
    text = ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if not text:
        return False, "", "Failed to decode TXT file. The file may contain unsupported binary data."

    cleaned = text.strip()
    if not cleaned:
        return False, "", "TXT file contains no readable text."

    if len(cleaned) > MAX_TEXT_CHAR_LIMIT:
        cleaned = cleaned[:MAX_TEXT_CHAR_LIMIT]

    return True, cleaned, None


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Extracts text from uploaded text-based PDF bytes using pypdf.
    Returns: (is_valid: bool, extracted_text: str, error_message: Optional[str])
    """
    if not file_bytes:
        return False, "", "PDF file is empty (0 bytes)."

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, "", f"File size ({len(file_bytes)} bytes) exceeds maximum allowed limit of 5 MB."

    try:
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)

        if reader.is_encrypted:
            # Attempt to decrypt with empty password for PDFs with empty user passwords
            try:
                decrypted = reader.decrypt("")
                if decrypted == 0:
                    return False, "", "PDF is password-protected. Please upload an unprotected file."
            except Exception:
                return False, "", "PDF is password-protected or encrypted. Please upload an unprotected file."

        num_pages = len(reader.pages)
        if num_pages == 0:
            return False, "", "PDF file contains no pages."

        extracted_pages = []
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            return (
                False,
                "",
                "No extractable text was found in this PDF. It appears to be a scanned image or empty. "
                "LocalLedger AI does not include OCR in this version; please paste the invoice text manually.",
            )

        if len(full_text) > MAX_TEXT_CHAR_LIMIT:
            full_text = full_text[:MAX_TEXT_CHAR_LIMIT]

        return True, full_text, None

    except PdfReadError as pre:
        return False, "", f"Malformed or corrupted PDF file: {str(pre)}"
    except Exception as exc:
        return False, "", f"Failed to parse PDF document: {str(exc)}"


def extract_text_from_upload(filename: str, file_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Routes an uploaded file (by filename and bytes) to the appropriate text extractor.
    Enforces extension checks, file size bounds, and safety limits.
    Returns: (is_valid: bool, extracted_text: str, error_message: Optional[str])
    """
    if not filename or not isinstance(filename, str):
        return False, "", "Invalid filename."

    # Prevent directory traversal in filename
    clean_filename = filename.replace("\\", "/").split("/")[-1]
    dot_idx = clean_filename.rfind(".")
    if dot_idx == -1:
        return False, "", "Uploaded file has no extension. Only .txt and .pdf files are supported."

    ext = clean_filename[dot_idx:].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "", f"Unsupported file type '{ext}'. Only .txt and .pdf files are accepted."

    if ext == ".txt":
        return extract_text_from_txt(file_bytes)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    else:
        return False, "", f"Unsupported file extension: {ext}"


def process_invoice_document(
    input_source: Union[str, bytes],
    filename: Optional[str] = None,
    base_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
    timeout: float = 60.0,
) -> Tuple[bool, str, Dict[str, Any], List[str], Optional[str]]:
    """
    End-to-end processing pipeline connecting invoice parsing to AI extraction.

    Accepts:
    - input_source: Either pasted text (str) OR raw file content (bytes) from an upload.
    - filename: Name of uploaded file if input_source is bytes (e.g. 'invoice.pdf').
    - base_url: Ollama API URL.
    - model: Target Ollama model name.
    - timeout: Request timeout in seconds.

    Returns:
    (success: bool, raw_text: str, fields: Dict[str, Any], warnings: List[str], error: Optional[str])

    Guarantees:
    - No persistent disk writes of documents or databases.
    - Input treated as untrusted data.
    - Clean error propagation if Ollama is unreachable, model is missing, or extraction fails.
    """
    raw_text = ""

    # 1. Extract and sanitize raw text from input
    if isinstance(input_source, bytes):
        if not filename:
            return False, "", {}, [], "Uploaded file content provided without a filename."
        valid, extracted, err = extract_text_from_upload(filename, input_source)
        if not valid:
            return False, "", {}, [], err
        raw_text = extracted
    elif isinstance(input_source, str):
        valid, cleaned, err = validate_pasted_text(input_source)
        if not valid:
            return False, "", {}, [], err
        raw_text = cleaned
    else:
        return False, "", {}, [], f"Unsupported input type: {type(input_source).__name__}."

    if not raw_text.strip():
        return False, "", {}, [], "Extracted document text is empty."

    # 2. Invoke local AI extraction service
    ai_success, extracted_fields, ai_error = extract_invoice_data(
        invoice_text=raw_text,
        base_url=base_url,
        model=model,
        timeout=timeout,
    )

    if not ai_success:
        return False, raw_text, {}, [], ai_error

    # 3. Canonical validation and arithmetic checks
    cleaned_fields, warnings = validate_and_clean_invoice_data(extracted_fields)

    return True, raw_text, cleaned_fields, warnings, None

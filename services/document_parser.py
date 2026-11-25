from __future__ import annotations

import io
import os
import re
from typing import Tuple


class DocumentParseError(Exception):
    """Raised when an uploaded resume cannot be validated or parsed."""


def clean_extracted_text(raw_text: str) -> str:
    """Normalize whitespace and strip null bytes from extracted resume text."""
    cleaned = raw_text.replace("\x00", " ").replace("\r\n", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract readable text from PDF bytes using PyMuPDF."""
    import pymupdf

    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise DocumentParseError("Unable to open PDF document. Please verify the file is not corrupted.") from exc

    try:
        pages_text = [page.get_text("text") for page in doc]
    finally:
        doc.close()

    return clean_extracted_text("\n".join(pages_text))


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from Word (.docx) paragraphs and tables using python-docx."""
    from docx import Document

    try:
        document = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentParseError("Unable to open Word (.docx) document. Please verify the file is valid.") from exc

    segments: list[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text and paragraph.text.strip():
            segments.append(paragraph.text.strip())

    for table in document.tables:
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text and cell.text.strip()]
            if row_cells:
                segments.append(" | ".join(row_cells))

    return clean_extracted_text("\n".join(segments))


def extract_text_from_bytes(
    file_bytes: bytes,
    filename: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> Tuple[str, str]:
    """
    Validate and extract text from an uploaded PDF, DOCX, or TXT file.

    Returns:
        Tuple of (extracted_text, normalized_file_type_label)
    """
    if not file_bytes:
        raise DocumentParseError("The uploaded file appears to be empty.")

    if len(file_bytes) > max_bytes:
        raise DocumentParseError("File size exceeds the 5MB maximum limit.")

    _, ext = os.path.splitext(filename.lower())

    if ext == ".pdf":
        text = extract_text_from_pdf(file_bytes)
        file_type = "PDF"
    elif ext == ".docx":
        text = extract_text_from_docx(file_bytes)
        file_type = "DOCX"
    elif ext == ".txt":
        try:
            text = clean_extracted_text(file_bytes.decode("utf-8"))
        except UnicodeDecodeError:
            text = clean_extracted_text(file_bytes.decode("latin-1", errors="ignore"))
        file_type = "TXT"
    else:
        raise DocumentParseError(
            "Unsupported file format. Please upload a PDF (.pdf) or Word (.docx) document."
        )

    if len(text.strip()) < 20:
        raise DocumentParseError(
            "No readable text could be extracted from this file. Please ensure the PDF/DOCX is not an image-only scan."
        )

    return text, file_type

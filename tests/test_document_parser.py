from __future__ import annotations

import io

import pymupdf
import pytest
from docx import Document

from services.document_parser import DocumentParseError, extract_text_from_bytes


def build_sample_pdf_bytes(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def build_sample_docx_bytes(paragraphs: list[str], table_rows: list[list[str]] | None = None) -> bytes:
    document = Document()
    for p in paragraphs:
        document.add_paragraph(p)
    if table_rows:
        table = document.add_table(rows=len(table_rows), cols=len(table_rows[0]))
        for r_idx, row in enumerate(table_rows):
            for c_idx, val in enumerate(row):
                table.cell(r_idx, c_idx).text = val
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def test_extract_text_from_real_pdf():
    sample_text = "Alexander Patel\nSkills: Python, Flask, spaCy, scikit-learn, PostgreSQL"
    pdf_bytes = build_sample_pdf_bytes(sample_text)

    extracted, file_type = extract_text_from_bytes(pdf_bytes, "resume.pdf")
    assert file_type == "PDF"
    assert "Python" in extracted
    assert "scikit-learn" in extracted


def test_extract_text_from_real_docx_including_tables():
    docx_bytes = build_sample_docx_bytes(
        paragraphs=["Candidate Resume", "Experienced in Python and Flask APIs."],
        table_rows=[["Core NLP", "spaCy, scikit-learn, PyMuPDF"]],
    )

    extracted, file_type = extract_text_from_bytes(docx_bytes, "candidate_cv.docx")
    assert file_type == "DOCX"
    assert "Flask" in extracted
    assert "PyMuPDF" in extracted


def test_rejects_unsupported_extension():
    with pytest.raises(DocumentParseError, match="Unsupported file format"):
        extract_text_from_bytes(b"hello world resume content", "resume.exe")


def test_rejects_empty_bytes():
    with pytest.raises(DocumentParseError, match="empty"):
        extract_text_from_bytes(b"", "resume.pdf")


def test_rejects_oversized_file():
    oversized = b"a" * (5 * 1024 * 1024 + 10)
    with pytest.raises(DocumentParseError, match="5MB"):
        extract_text_from_bytes(oversized, "large.txt")

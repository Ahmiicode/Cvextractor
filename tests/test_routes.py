from __future__ import annotations

import io
import zipfile

import pymupdf
import pytest
from docx import Document

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _make_pdf_bytes(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _make_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def test_landing_and_dashboard_routes(client):
    landing_res = client.get("/")
    assert landing_res.status_code == 200
    assert b"SkillAlign" in landing_res.data
    assert b"AI-Powered Resume to" in landing_res.data

    dash_res = client.get("/dashboard")
    assert dash_res.status_code == 200
    assert b"Resume Scanner" in dash_res.data


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["status"] == "ok"


def test_api_analyze_with_real_pdf(client):
    pdf_bytes = _make_pdf_bytes(
        "Alexander Patel\nSkills: Python, Flask, spaCy, scikit-learn, PyMuPDF, PostgreSQL, Docker"
    )
    jd = (
        "Looking for a Python Flask engineer skilled in spaCy, scikit-learn, "
        "PostgreSQL, Docker, and AWS deployment."
    )

    res = client.post(
        "/api/analyze",
        data={
            "resume": (io.BytesIO(pdf_bytes), "candidate.pdf"),
            "jobDescription": jd,
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 200
    data = res.get_json()
    assert data["fileType"] == "PDF"
    assert "Python" in data["matchedSkills"]
    assert "AWS" in data["missingSkills"]
    assert data["overallScore"] > 0


def test_api_analyze_with_real_docx(client):
    docx_bytes = _make_docx_bytes(
        "Software Engineer with Python, Flask, spaCy, scikit-learn, and HTML5/CSS3."
    )
    jd = "Seeking a Python Flask engineer with spaCy, scikit-learn, and PostgreSQL experience."

    res = client.post(
        "/api/analyze",
        data={
            "resume": (io.BytesIO(docx_bytes), "resume.docx"),
            "jobDescription": jd,
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 200
    data = res.get_json()
    assert data["fileType"] == "DOCX"
    assert "Flask" in data["matchedSkills"]
    assert "PostgreSQL" in data["missingSkills"]


def test_api_analyze_validation_errors(client):
    # Missing file
    res_no_file = client.post(
        "/api/analyze",
        data={"jobDescription": "Seeking a Python Flask NLP engineer with spaCy."},
    )
    assert res_no_file.status_code == 400

    # Short job description
    res_short_jd = client.post(
        "/api/analyze",
        data={
            "resume": (io.BytesIO(b"Python developer resume text"), "cv.txt"),
            "jobDescription": "Too short",
        },
        content_type="multipart/form-data",
    )
    assert res_short_jd.status_code == 400

    # Unsupported extension
    res_bad_ext = client.post(
        "/api/analyze",
        data={
            "resume": (io.BytesIO(b"binary"), "cv.png"),
            "jobDescription": "Seeking a Python Flask NLP engineer with spaCy.",
        },
        content_type="multipart/form-data",
    )
    assert res_bad_ext.status_code == 400


def test_download_project_zip(client):
    res = client.get("/download-project")
    assert res.status_code == 200
    assert res.mimetype == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(res.data))
    names = set(zf.namelist())
    assert "skillalign/app.py" in names
    assert "skillalign/config.py" in names
    assert "skillalign/requirements.txt" in names
    assert "skillalign/Procfile" in names
    assert "skillalign/templates/dashboard.html" in names
    assert "skillalign/static/js/dashboard.js" in names


from __future__ import annotations

import os
import traceback

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from services.document_parser import (
    DocumentParseError,
    extract_text_from_bytes,
)
from services.matcher_service import analyze_resume_against_job


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "SkillAlign Flask NLP Engine"
    })


@api_bp.post("/analyze")
def analyze_resume():
    """
    Analyze an uploaded resume against a job description.
    Supports PDF, DOCX and TXT files.
    """

    if "resume" not in request.files:
        return jsonify({
            "error": "Please upload a resume file (.pdf or .docx)."
        }), 400

    uploaded_file = request.files["resume"]

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({
            "error": "Please select a valid resume file (.pdf or .docx)."
        }), 400

    original_name = uploaded_file.filename
    safe_name = secure_filename(original_name) or original_name

    _, ext = os.path.splitext(original_name.lower())

    allowed_exts = {
        f".{item}"
        for item in current_app.config["ALLOWED_EXTENSIONS"]
    }

    if ext not in allowed_exts:
        return jsonify({
            "error": "Unsupported file format. Please upload a PDF (.pdf) or Word (.docx) document."
        }), 400

    job_description = (
        request.form.get("jobDescription") or ""
    ).strip()

    if len(job_description) < 30:
        return jsonify({
            "error": "Please enter a job description of at least 30 characters for accurate NLP matching."
        }), 400

    file_bytes = uploaded_file.read()

    max_bytes = int(
        current_app.config.get(
            "MAX_CONTENT_LENGTH",
            5 * 1024 * 1024
        )
    )

    try:
        resume_text, file_type = extract_text_from_bytes(
            file_bytes=file_bytes,
            filename=original_name,
            max_bytes=max_bytes,
        )

    except DocumentParseError as exc:
        status_code = (
            422
            if "readable text" in str(exc).lower()
            else 400
        )

        return jsonify({
            "error": str(exc)
        }), status_code

    except Exception as exc:
        print("DOCUMENT EXTRACTION ERROR:")
        traceback.print_exc()

        return jsonify({
            "error": "Document extraction failed.",
            "details": str(exc)
        }), 500

    try:
        result = analyze_resume_against_job(
            resume_text=resume_text,
            job_description=job_description,
            file_name=original_name or safe_name,
            file_size_bytes=len(file_bytes),
            file_type=file_type,
        )

        return jsonify(result), 200

    except Exception as exc:
        print("RESUME ANALYSIS ERROR:")
        traceback.print_exc()

        return jsonify({
            "error": "Resume analysis failed.",
            "details": str(exc)
        }), 500

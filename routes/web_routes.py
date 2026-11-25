from __future__ import annotations

import io
import os
import zipfile

from flask import Blueprint, current_app, render_template, request, send_file

web_bp = Blueprint("web", __name__)

VALID_SECTIONS = {"dashboard", "scanner", "results", "how-it-works", "about"}

INCLUDED_ROOT_FILES = {
    "app.py",
    "config.py",
    "requirements.txt",
    "Procfile",
    "render.yaml",
    "README.md",
    ".env.example",
    ".gitignore",
}

INCLUDED_DIRS = {"routes", "services", "templates", "static", "tests"}
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".venv", "venv", ".git"}


@web_bp.get("/")
def landing():
    """Render the SkillAlign landing page."""
    return render_template("landing.html")


@web_bp.get("/dashboard")
def dashboard():
    """Render the SkillAlign main application dashboard."""
    requested = request.args.get("section", "dashboard")
    initial_section = requested if requested in VALID_SECTIONS else "dashboard"
    return render_template("dashboard.html", initial_section=initial_section)


@web_bp.get("/download-project")
def download_project_zip():
    """Package and download the complete SkillAlign Python Flask project as a ZIP archive."""
    root_dir = current_app.root_path
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in sorted(INCLUDED_ROOT_FILES):
            full_path = os.path.join(root_dir, filename)
            if os.path.isfile(full_path):
                zf.write(full_path, arcname=os.path.join("skillalign", filename))

        for folder in sorted(INCLUDED_DIRS):
            folder_path = os.path.join(root_dir, folder)
            if not os.path.isdir(folder_path):
                continue
            for dirpath, dirnames, filenames in os.walk(folder_path):
                dirnames[:] = [d for d in sorted(dirnames) if d not in EXCLUDED_NAMES]
                for fname in sorted(filenames):
                    if fname.endswith((".pyc", ".pyo")) or fname in EXCLUDED_NAMES:
                        continue
                    abs_file = os.path.join(dirpath, fname)
                    rel_file = os.path.relpath(abs_file, root_dir)
                    zf.write(abs_file, arcname=os.path.join("skillalign", rel_file))

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="skillalign.zip",
    )

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration for the SkillAlign Flask server."""

    SECRET_KEY = os.getenv("SECRET_KEY", "skillalign-cn6000-dev-secret")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload cap
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
    PORT = int(os.getenv("PORT", "5001"))
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

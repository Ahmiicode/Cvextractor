from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from routes.api_routes import api_bp
from routes.web_routes import web_bp


def create_app(config_object=Config) -> Flask:
    """Create and configure the SkillAlign Flask application."""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(_err):
        return jsonify({"error": "File size exceeds the 5MB maximum limit."}), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

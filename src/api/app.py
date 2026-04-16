"""Flask application factory for OpenPrinterAgent."""

from typing import Any

from flask import Flask, jsonify
from flask_cors import CORS

from src.core.exceptions import (
    ConfigurationError,
    JobError,
    OpenPrinterAgentError,
    PrinterError,
)
from src.utils.config import Config, load_config


def create_app(config: Config | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional Config instance. If not provided, loads from environment.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    if config is None:
        config = load_config()

    app.config["SECRET_KEY"] = config.API_SECRET_KEY
    app.config["DEBUG"] = config.FLASK_DEBUG
    app.config["API_KEY"] = config.API_KEY

    CORS(
        app,
        origins=config.get_cors_origins(),
        supports_credentials=True,
    )

    _register_error_handlers(app)
    _register_api_routes(app)

    return app


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application.

    Args:
        app: Flask application instance.
    """

    @app.errorhandler(400)
    def bad_request(error: Any) -> tuple[Any, int]:
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error: Any) -> tuple[Any, int]:
        return jsonify({"error": "Unauthorized", "message": "Invalid API key"}), 401

    @app.errorhandler(404)
    def not_found(error: Any) -> tuple[Any, int]:
        return jsonify({"error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[Any, int]:
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

    @app.errorhandler(PrinterError)
    def handle_printer_error(error: PrinterError) -> tuple[Any, int]:
        return jsonify({"error": "Printer Error", "message": error.message}), 400

    @app.errorhandler(JobError)
    def handle_job_error(error: JobError) -> tuple[Any, int]:
        return jsonify({"error": "Job Error", "message": error.message}), 400

    @app.errorhandler(ConfigurationError)
    def handle_config_error(error: ConfigurationError) -> tuple[Any, int]:
        return jsonify({"error": "Configuration Error", "message": error.message}), 500

    @app.errorhandler(OpenPrinterAgentError)
    def handle_generic_error(error: OpenPrinterAgentError) -> tuple[Any, int]:
        return jsonify({"error": "Error", "message": error.message}), 500


def _register_api_routes(app: Flask) -> None:
    """Register API route blueprints.

    Args:
        app: Flask application instance.
    """
    from src.api.routes.print_jobs import print_jobs_bp
    from src.api.routes.printers import printers_bp
    from src.api.routes.status import status_bp

    app.register_blueprint(printers_bp, url_prefix="/api/printers")
    app.register_blueprint(print_jobs_bp, url_prefix="/api")
    app.register_blueprint(status_bp, url_prefix="/api")

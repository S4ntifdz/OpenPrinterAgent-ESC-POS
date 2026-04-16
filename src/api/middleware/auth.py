"""API key authentication middleware for OpenPrinterAgent."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import current_app, jsonify, request


def require_api_key(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require API key authentication.

    Args:
        f: The function to wrap.

    Returns:
        Wrapped function that checks for valid API key.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return jsonify({"error": "Unauthorized", "message": "API key required"}), 401

        expected_key = current_app.config.get("API_KEY")
        if expected_key and api_key != expected_key:
            return jsonify({"error": "Unauthorized", "message": "Invalid API key"}), 401

        return f(*args, **kwargs)

    return decorated_function

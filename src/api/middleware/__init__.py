"""Middleware for OpenPrinterAgent API."""

from src.api.middleware.auth import require_api_key

__all__ = ["require_api_key"]

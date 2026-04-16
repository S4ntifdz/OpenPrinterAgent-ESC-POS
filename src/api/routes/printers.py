"""Printer management API routes."""

from typing import Any

from flask import Blueprint, jsonify, request

from src.api.middleware.auth import require_api_key
from src.api.schemas.validators import CreatePrinterSchema
from src.core.entities import ConnectionType
from src.core.exceptions import PrinterError
from src.models.database import Database
from src.services.printer_service import PrinterService

printers_bp = Blueprint("printers", __name__)


def _get_printer_service() -> PrinterService:
    """Get PrinterService instance.

    Returns:
        PrinterService instance.
    """
    from src.utils.config import get_config

    config = get_config()
    db = Database(config.DATABASE_PATH)
    db.init_schema()
    return PrinterService(db)


@printers_bp.route("", methods=["GET"])
@require_api_key
def list_printers() -> tuple[dict[str, list[dict]], int]:
    """List all printers.

    Returns:
        JSON response with list of printers.
    """
    service = _get_printer_service()
    printers = service.list_printers()
    return jsonify({"printers": [p.to_dict() for p in printers]}), 200


@printers_bp.route("", methods=["POST"])
@require_api_key
def create_printer() -> tuple[dict[str, Any], int]:
    """Create a new printer.

    Returns:
        JSON response with created printer or error.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Bad Request", "message": "JSON body required"}), 400

    schema = CreatePrinterSchema.from_dict(data)
    errors = schema.validate()
    if errors:
        return jsonify({"error": "Validation Error", "message": "; ".join(errors)}), 400

    service = _get_printer_service()

    try:
        connection_type = ConnectionType(schema.connection_type)
        printer = service.add_printer(
            name=schema.name,
            connection_type=connection_type,
            vendor_id=schema.vendor_id,
            product_id=schema.product_id,
            port=schema.port,
            baudrate=schema.baudrate,
        )
        return jsonify({"printer": printer.to_dict()}), 201
    except PrinterError as e:
        return jsonify({"error": "Printer Error", "message": e.message}), 400


@printers_bp.route("/<printer_id>", methods=["GET"])
@require_api_key
def get_printer(printer_id: str) -> tuple[dict[str, Any], int]:
    """Get a printer by ID.

    Args:
        printer_id: ID of the printer.

    Returns:
        JSON response with printer or error.
    """
    service = _get_printer_service()
    printer = service.get_printer(printer_id)

    if printer is None:
        return jsonify({"error": "Not Found", "message": "Printer not found"}), 404

    return jsonify({"printer": printer.to_dict()}), 200


@printers_bp.route("/<printer_id>", methods=["DELETE"])
@require_api_key
def delete_printer(printer_id: str) -> tuple[dict[str, Any], int]:
    """Delete a printer.

    Args:
        printer_id: ID of the printer.

    Returns:
        JSON response confirming deletion or error.
    """
    service = _get_printer_service()
    printer = service.get_printer(printer_id)

    if printer is None:
        return jsonify({"error": "Not Found", "message": "Printer not found"}), 404

    service.remove_printer(printer_id)
    return jsonify({"message": "Printer deleted"}), 200


@printers_bp.route("/<printer_id>/connect", methods=["POST"])
@require_api_key
def connect_printer(printer_id: str) -> tuple[dict[str, Any], int]:
    """Connect to a printer.

    Args:
        printer_id: ID of the printer.

    Returns:
        JSON response with updated printer or error.
    """
    service = _get_printer_service()

    try:
        printer = service.connect_printer(printer_id)
        return jsonify({"printer": printer.to_dict()}), 200
    except PrinterError as e:
        return jsonify({"error": "Printer Error", "message": e.message}), 400


@printers_bp.route("/<printer_id>/disconnect", methods=["POST"])
@require_api_key
def disconnect_printer(printer_id: str) -> tuple[dict[str, Any], int]:
    """Disconnect from a printer.

    Args:
        printer_id: ID of the printer.

    Returns:
        JSON response with updated printer or error.
    """
    service = _get_printer_service()

    try:
        printer = service.disconnect_printer(printer_id)
        return jsonify({"printer": printer.to_dict()}), 200
    except PrinterError as e:
        return jsonify({"error": "Printer Error", "message": e.message}), 400

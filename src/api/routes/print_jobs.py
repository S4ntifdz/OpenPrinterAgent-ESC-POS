"""Print job API routes."""

from typing import Any

from flask import Blueprint, jsonify, request

from src.api.middleware.auth import require_api_key
from src.api.schemas.validators import (
    PrintBarcodeSchema,
    PrintQRCodeSchema,
    PrintTextSchema,
)
from src.core.entities import JobStatus
from src.core.exceptions import JobError, PrinterError
from src.models.database import Database
from src.services.job_service import JobService
from src.services.print_service import PrintService
from src.services.printer_service import PrinterService

print_jobs_bp = Blueprint("print_jobs", __name__)


def _get_services():
    """Get service instances.

    Returns:
        Tuple of (PrinterService, PrintService, JobService).
    """
    from src.utils.config import get_config

    config = get_config()
    db = Database(config.DATABASE_PATH)
    db.init_schema()

    printer_service = PrinterService(db)
    print_service = PrintService(printer_service)
    job_service = JobService(db)

    return printer_service, print_service, job_service


@print_jobs_bp.route("/print", methods=["POST"])
@require_api_key
def print_content() -> tuple[dict[str, Any], int]:
    """Send a print job to a printer.

    Returns:
        JSON response with job ID or error.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Bad Request", "message": "JSON body required"}), 400

    job_type = data.get("type", "text")
    printer_service, print_service, job_service = _get_services()

    try:
        if job_type == "text":
            schema = PrintTextSchema.from_dict(data)
            errors = schema.validate()
            if errors:
                return jsonify({"error": "Validation Error", "message": "; ".join(errors)}), 400

            job = print_service.print_text(
                schema.printer_id,
                schema.text,
                bold=schema.bold,
                double_height=schema.double_height,
                double_width=schema.double_width,
            )

        elif job_type == "barcode":
            schema = PrintBarcodeSchema.from_dict(data)
            errors = schema.validate()
            if errors:
                return jsonify({"error": "Validation Error", "message": "; ".join(errors)}), 400

            job = print_service.print_barcode(
                schema.printer_id,
                schema.data,
                barcode_type=schema.barcode_type,
                height=schema.height,
                width=schema.width,
            )

        elif job_type == "qrcode":
            schema = PrintQRCodeSchema.from_dict(data)
            errors = schema.validate()
            if errors:
                return jsonify({"error": "Validation Error", "message": "; ".join(errors)}), 400

            job = print_service.print_qrcode(
                schema.printer_id,
                schema.data,
                size=schema.size,
                error_correction=schema.error_correction,
            )

        else:
            return jsonify(
                {"error": "Validation Error", "message": f"Unknown job type: {job_type}"}
            ), 400

        job_service.create_job(
            printer_id=job.printer_id,
            job_type=job.type,
            content=job.content,
        )

        return jsonify({"job_id": job.id, "status": job.status.value}), 202

    except PrinterError as e:
        return jsonify({"error": "Printer Error", "message": e.message}), 400
    except JobError as e:
        return jsonify({"error": "Job Error", "message": e.message}), 400


@print_jobs_bp.route("/jobs", methods=["GET"])
@require_api_key
def list_jobs() -> tuple[dict[str, Any], int]:
    """List print jobs with optional filters.

    Returns:
        JSON response with list of jobs.
    """
    printer_id = request.args.get("printer_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 100))

    _, _, job_service = _get_services()

    job_status = None
    if status:
        try:
            job_status = JobStatus(status)
        except ValueError:
            return jsonify({"error": "Validation Error", "message": "Invalid status value"}), 400

    jobs = job_service.list_jobs(printer_id=printer_id, status=job_status, limit=limit)
    return jsonify({"jobs": [j.to_dict() for j in jobs]}), 200


@print_jobs_bp.route("/jobs/<job_id>", methods=["GET"])
@require_api_key
def get_job(job_id: str) -> tuple[dict[str, Any], int]:
    """Get a print job by ID.

    Args:
        job_id: ID of the print job.

    Returns:
        JSON response with job or error.
    """
    _, _, job_service = _get_services()
    job = job_service.get_job(job_id)

    if job is None:
        return jsonify({"error": "Not Found", "message": "Job not found"}), 404

    return jsonify({"job": job.to_dict()}), 200


@print_jobs_bp.route("/jobs/<job_id>", methods=["DELETE"])
@require_api_key
def cancel_job(job_id: str) -> tuple[dict[str, Any], int]:
    """Cancel a print job.

    Args:
        job_id: ID of the print job.

    Returns:
        JSON response confirming cancellation or error.
    """
    _, _, job_service = _get_services()

    try:
        job = job_service.cancel_job(job_id)
        if job is None:
            return jsonify({"error": "Not Found", "message": "Job not found"}), 404
        return jsonify({"job": job.to_dict()}), 200
    except JobError as e:
        return jsonify({"error": "Job Error", "message": e.message}), 400

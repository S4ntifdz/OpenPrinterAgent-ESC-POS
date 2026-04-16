"""System status API routes."""

import time
from typing import Any

from flask import Blueprint, jsonify

from src.core.entities import JobStatus, PrinterStatus
from src.models.database import Database
from src.services.job_service import JobService
from src.services.printer_service import PrinterService
from src.utils.config import get_config

status_bp = Blueprint("status", __name__)

_start_time = time.time()


@status_bp.route("/status", methods=["GET"])
def get_status() -> tuple[dict[str, Any], int]:
    """Get system status.

    This endpoint is public (no authentication required).

    Returns:
        JSON response with system metrics.
    """
    config = get_config()
    db = Database(config.DATABASE_PATH)
    db.init_schema()

    printer_service = PrinterService(db)
    job_service = JobService(db)

    printers = printer_service.list_printers()
    connected_printers = sum(1 for p in printers if p.status == PrinterStatus.CONNECTED)
    pending_jobs = job_service.list_jobs(status=JobStatus.PENDING, limit=1000)
    jobs_pending = len(pending_jobs)

    uptime = int(time.time() - _start_time)

    return jsonify(
        {
            "status": "ok",
            "printers_connected": connected_printers,
            "printers_total": len(printers),
            "jobs_pending": jobs_pending,
            "uptime_seconds": uptime,
        }
    ), 200

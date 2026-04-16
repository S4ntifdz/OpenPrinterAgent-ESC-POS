"""API routes for OpenPrinterAgent."""

from src.api.routes.print_jobs import print_jobs_bp
from src.api.routes.printers import printers_bp
from src.api.routes.status import status_bp

__all__ = ["printers_bp", "print_jobs_bp", "status_bp"]

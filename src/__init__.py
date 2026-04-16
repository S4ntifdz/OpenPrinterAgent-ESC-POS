"""OpenPrinterAgent - Desktop application for ESC/POS thermal printer control."""

__author__ = "OpenPrinterAgent Team"
__version__ = "0.1.0"

from src.core.entities import Printer, PrintJob
from src.core.exceptions import ConnectionError, JobError, PrinterError

__all__ = [
    "ConnectionError",
    "JobError",
    "Printer",
    "PrinterError",
    "PrintJob",
]

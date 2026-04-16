"""Core domain module for OpenPrinterAgent.

This module contains the core entities and exceptions that form the
domain model of the application.
"""

from src.core.entities import (
    ConnectionType,
    JobStatus,
    JobType,
    Printer,
    PrinterStatus,
    PrintJob,
)
from src.core.exceptions import (
    ConfigurationError,
    ConnectionError,
    DriverError,
    JobError,
    OpenPrinterAgentError,
    PrinterError,
    ValidationError,
)

__all__ = [
    # Enums
    "ConnectionType",
    "JobStatus",
    "JobType",
    "PrinterStatus",
    # Entities
    "Printer",
    "PrintJob",
    # Exceptions
    "OpenPrinterAgentError",
    "PrinterError",
    "ConnectionError",
    "JobError",
    "DriverError",
    "ConfigurationError",
    "ValidationError",
]

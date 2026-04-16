"""Core domain entities for OpenPrinterAgent."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class ConnectionType(Enum):
    """Printer connection type enumeration."""

    USB = "usb"
    SERIAL = "serial"


class PrinterStatus(Enum):
    """Printer status enumeration."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class JobType(Enum):
    """Print job type enumeration."""

    TEXT = "text"
    IMAGE = "image"
    BARCODE = "barcode"
    QRCODE = "qrcode"


class JobStatus(Enum):
    """Print job status enumeration."""

    PENDING = "pending"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Printer:
    """Printer entity representing a physical or virtual printer device.

    Attributes:
        id: Unique identifier for the printer.
        name: Human-readable name for the printer.
        connection_type: Connection method (USB or Serial).
        vendor_id: USB vendor ID (only for USB connections).
        product_id: USB product ID (only for USB connections).
        port: Serial port path (only for Serial connections).
        baudrate: Serial baud rate (default: 9600).
        status: Current printer status.
        created_at: Timestamp when the printer was created.
        updated_at: Timestamp when the printer was last updated.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    connection_type: ConnectionType = ConnectionType.USB
    vendor_id: int | None = None
    product_id: int | None = None
    port: str | None = None
    baudrate: int = 9600
    status: PrinterStatus = PrinterStatus.DISCONNECTED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate printer entity after initialization."""
        if not self.name:
            raise ValueError("Printer name cannot be empty")
        if self.connection_type == ConnectionType.USB and (
            self.vendor_id is None or self.product_id is None
        ):
            raise ValueError("USB printers require vendor_id and product_id")
        if self.connection_type == ConnectionType.SERIAL and not self.port:
            raise ValueError("Serial printers require a port")

    def to_dict(self) -> dict[str, Any]:
        """Convert printer entity to dictionary.

        Returns:
            Dictionary representation of the printer.
        """
        return {
            "id": self.id,
            "name": self.name,
            "connection_type": self.connection_type.value,
            "vendor_id": self.vendor_id,
            "product_id": self.product_id,
            "port": self.port,
            "baudrate": self.baudrate,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Printer":
        """Create printer entity from dictionary.

        Args:
            data: Dictionary containing printer data.

        Returns:
            Printer instance.
        """
        return cls(
            id=data.get("id", str(uuid4())),
            name=data["name"],
            connection_type=ConnectionType(data["connection_type"]),
            vendor_id=data.get("vendor_id"),
            product_id=data.get("product_id"),
            port=data.get("port"),
            baudrate=data.get("baudrate", 9600),
            status=PrinterStatus(data.get("status", "disconnected")),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(timezone.utc),
        )


@dataclass
class PrintJob:
    """Print job entity representing a printing task.

    Attributes:
        id: Unique identifier for the job.
        printer_id: ID of the printer to use.
        type: Type of print job (text, image, barcode, qrcode).
        content: Content to print (format depends on type).
        status: Current job status.
        error: Error message if job failed.
        created_at: Timestamp when the job was created.
        started_at: Timestamp when printing started.
        completed_at: Timestamp when printing completed.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    printer_id: str = ""
    type: JobType = JobType.TEXT
    content: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate print job entity after initialization."""
        if not self.printer_id:
            raise ValueError("Print job requires a printer_id")
        if not self.content:
            raise ValueError("Print job requires content")

    def to_dict(self) -> dict[str, Any]:
        """Convert print job entity to dictionary.

        Returns:
            Dictionary representation of the print job.
        """
        return {
            "id": self.id,
            "printer_id": self.printer_id,
            "type": self.type.value,
            "content": self.content,
            "status": self.status.value,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrintJob":
        """Create print job entity from dictionary.

        Args:
            data: Dictionary containing print job data.

        Returns:
            PrintJob instance.
        """
        return cls(
            id=data.get("id", str(uuid4())),
            printer_id=data["printer_id"],
            type=JobType(data["type"]),
            content=data["content"],
            status=JobStatus(data.get("status", "pending")),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(timezone.utc),
            started_at=datetime.fromisoformat(data["started_at"]) if "started_at" in data else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if "completed_at" in data
            else None,
        )

    def mark_started(self) -> None:
        """Mark the job as started (printing in progress)."""
        self.status = JobStatus.PRINTING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        """Mark the job as completed successfully."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.error = None

    def mark_failed(self, error_message: str) -> None:
        """Mark the job as failed.

        Args:
            error_message: Description of the error.
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = error_message

    def mark_cancelled(self) -> None:
        """Mark the job as cancelled (only if pending)."""
        if self.status == JobStatus.PENDING:
            self.status = JobStatus.CANCELLED
            self.completed_at = datetime.now(timezone.utc)

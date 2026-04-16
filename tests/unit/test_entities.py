"""Unit tests for core domain entities."""


import pytest

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
    PrinterError,
    ValidationError,
)


class TestConnectionType:
    """Tests for ConnectionType enum."""

    def test_usb_value(self) -> None:
        """Test USB connection type value."""
        assert ConnectionType.USB.value == "usb"

    def test_serial_value(self) -> None:
        """Test Serial connection type value."""
        assert ConnectionType.SERIAL.value == "serial"

    def test_all_values(self, connection_types: list[ConnectionType]) -> None:
        """Test all connection types are defined."""
        assert len(connection_types) == 2
        assert ConnectionType.USB in connection_types
        assert ConnectionType.SERIAL in connection_types


class TestPrinterStatus:
    """Tests for PrinterStatus enum."""

    def test_all_statuses(self, printer_statuses: list[PrinterStatus]) -> None:
        """Test all printer statuses are defined."""
        assert len(printer_statuses) == 3
        assert PrinterStatus.CONNECTED in printer_statuses
        assert PrinterStatus.DISCONNECTED in printer_statuses
        assert PrinterStatus.ERROR in printer_statuses


class TestJobType:
    """Tests for JobType enum."""

    def test_all_job_types(self, job_types: list[JobType]) -> None:
        """Test all job types are defined."""
        assert len(job_types) == 4
        assert JobType.TEXT in job_types
        assert JobType.IMAGE in job_types
        assert JobType.BARCODE in job_types
        assert JobType.QRCODE in job_types


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_all_job_statuses(self, job_statuses: list[JobStatus]) -> None:
        """Test all job statuses are defined."""
        assert len(job_statuses) == 5
        assert JobStatus.PENDING in job_statuses
        assert JobStatus.PRINTING in job_statuses
        assert JobStatus.COMPLETED in job_statuses
        assert JobStatus.FAILED in job_statuses
        assert JobStatus.CANCELLED in job_statuses


class TestPrinter:
    """Tests for Printer entity."""

    def test_create_usb_printer(self, usb_printer: Printer) -> None:
        """Test creating a USB printer."""
        assert usb_printer.name == "Test USB Printer"
        assert usb_printer.connection_type == ConnectionType.USB
        assert usb_printer.vendor_id == 0x04B8
        assert usb_printer.product_id == 0x0202
        assert usb_printer.status == PrinterStatus.DISCONNECTED

    def test_create_serial_printer(self, serial_printer: Printer) -> None:
        """Test creating a serial printer."""
        assert serial_printer.name == "Test Serial Printer"
        assert serial_printer.connection_type == ConnectionType.SERIAL
        assert serial_printer.port == "/dev/ttyUSB0"
        assert serial_printer.baudrate == 115200

    def test_printer_validation_empty_name(self) -> None:
        """Test printer validation rejects empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Printer(name="", connection_type=ConnectionType.USB)

    def test_printer_validation_usb_missing_ids(self) -> None:
        """Test USB printer validation requires vendor and product ID."""
        with pytest.raises(ValueError, match="USB printers require vendor_id and product_id"):
            Printer(
                name="Test",
                connection_type=ConnectionType.USB,
                vendor_id=None,
                product_id=None,
            )

    def test_printer_validation_serial_missing_port(self) -> None:
        """Test serial printer validation requires port."""
        with pytest.raises(ValueError, match="Serial printers require a port"):
            Printer(
                name="Test",
                connection_type=ConnectionType.SERIAL,
                port=None,
            )

    def test_printer_to_dict(self, usb_printer: Printer) -> None:
        """Test converting printer to dictionary."""
        data = usb_printer.to_dict()
        assert data["name"] == "Test USB Printer"
        assert data["connection_type"] == "usb"
        assert data["vendor_id"] == 0x04B8
        assert data["product_id"] == 0x0202
        assert "id" in data
        assert "created_at" in data

    def test_printer_from_dict(self, sample_printer_data: dict) -> None:
        """Test creating printer from dictionary."""
        printer = Printer.from_dict(sample_printer_data)
        assert printer.name == sample_printer_data["name"]
        assert printer.connection_type == ConnectionType.USB

    def test_printer_from_dict_roundtrip(self, usb_printer: Printer) -> None:
        """Test printer survives dict roundtrip."""
        data = usb_printer.to_dict()
        restored = Printer.from_dict(data)
        assert restored.id == usb_printer.id
        assert restored.name == usb_printer.name
        assert restored.connection_type == usb_printer.connection_type


class TestPrintJob:
    """Tests for PrintJob entity."""

    def test_create_text_job(self, text_print_job: PrintJob) -> None:
        """Test creating a text print job."""
        assert text_print_job.type == JobType.TEXT
        assert text_print_job.content == {"text": "Hello, World!"}
        assert text_print_job.status == JobStatus.PENDING
        assert text_print_job.error is None

    def test_create_barcode_job(self, barcode_print_job: PrintJob) -> None:
        """Test creating a barcode print job."""
        assert barcode_print_job.type == JobType.BARCODE
        assert barcode_print_job.content["format"] == "CODE128"
        assert barcode_print_job.content["data"] == "123456789"

    def test_create_qrcode_job(self, qrcode_print_job: PrintJob) -> None:
        """Test creating a QR code print job."""
        assert qrcode_print_job.type == JobType.QRCODE
        assert qrcode_print_job.content["data"] == "https://example.com"

    def test_create_image_job(self, image_print_job: PrintJob) -> None:
        """Test creating an image print job."""
        assert image_print_job.type == JobType.IMAGE
        assert "image_base64" in image_print_job.content

    def test_job_validation_missing_printer_id(self) -> None:
        """Test job validation requires printer_id."""
        with pytest.raises(ValueError, match="printer_id"):
            PrintJob(
                printer_id="",
                type=JobType.TEXT,
                content={"text": "test"},
            )

    def test_job_validation_missing_content(self) -> None:
        """Test job validation requires content."""
        with pytest.raises(ValueError, match="content"):
            PrintJob(
                printer_id="test-printer",
                type=JobType.TEXT,
                content={},
            )

    def test_job_to_dict(self, text_print_job: PrintJob) -> None:
        """Test converting job to dictionary."""
        data = text_print_job.to_dict()
        assert data["type"] == "text"
        assert data["content"] == {"text": "Hello, World!"}
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_job_from_dict(self, sample_print_job_data: dict) -> None:
        """Test creating job from dictionary."""
        job = PrintJob.from_dict(sample_print_job_data)
        assert job.printer_id == sample_print_job_data["printer_id"]
        assert job.type == JobType.TEXT

    def test_job_mark_started(self, text_print_job: PrintJob) -> None:
        """Test marking job as started."""
        text_print_job.mark_started()
        assert text_print_job.status == JobStatus.PRINTING
        assert text_print_job.started_at is not None

    def test_job_mark_completed(self, text_print_job: PrintJob) -> None:
        """Test marking job as completed."""
        text_print_job.mark_completed()
        assert text_print_job.status == JobStatus.COMPLETED
        assert text_print_job.completed_at is not None
        assert text_print_job.error is None

    def test_job_mark_failed(self, text_print_job: PrintJob) -> None:
        """Test marking job as failed."""
        text_print_job.mark_failed("Printer not connected")
        assert text_print_job.status == JobStatus.FAILED
        assert text_print_job.completed_at is not None
        assert text_print_job.error == "Printer not connected"

    def test_job_mark_cancelled(self, text_print_job: PrintJob) -> None:
        """Test cancelling a pending job."""
        text_print_job.mark_cancelled()
        assert text_print_job.status == JobStatus.CANCELLED
        assert text_print_job.completed_at is not None

    def test_job_mark_cancelled_only_if_pending(self, text_print_job: PrintJob) -> None:
        """Test cancelling only works on pending jobs."""
        text_print_job.mark_started()
        text_print_job.mark_cancelled()
        assert text_print_job.status == JobStatus.PRINTING


class TestExceptions:
    """Tests for custom exceptions hierarchy."""

    def test_printer_error(self) -> None:
        """Test PrinterError exception."""
        error = PrinterError("Printer failed")
        assert isinstance(error, PrinterError)
        assert isinstance(error, Exception)
        assert error.message == "Printer failed"

    def test_connection_error(self) -> None:
        """Test ConnectionError exception."""
        error = ConnectionError("Connection lost")
        assert isinstance(error, ConnectionError)
        assert error.message == "Connection lost"

    def test_job_error(self) -> None:
        """Test JobError exception."""
        error = JobError("Job failed")
        assert isinstance(error, JobError)
        assert error.message == "Job failed"

    def test_driver_error(self) -> None:
        """Test DriverError exception."""
        error = DriverError("Driver error")
        assert isinstance(error, DriverError)
        assert error.message == "Driver error"

    def test_configuration_error(self) -> None:
        """Test ConfigurationError exception."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, ConfigurationError)
        assert error.message == "Invalid config"

    def test_validation_error(self) -> None:
        """Test ValidationError exception."""
        error = ValidationError("Invalid input")
        assert isinstance(error, ValidationError)
        assert error.message == "Invalid input"

    def test_exception_hierarchy(self) -> None:
        """Test all exceptions inherit from base."""
        assert issubclass(PrinterError, Exception)
        assert issubclass(ConnectionError, Exception)
        assert issubclass(JobError, Exception)
        assert issubclass(DriverError, Exception)
        assert issubclass(ConfigurationError, Exception)
        assert issubclass(ValidationError, Exception)

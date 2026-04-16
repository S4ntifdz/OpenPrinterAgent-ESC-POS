"""Pytest configuration and fixtures for OpenPrinterAgent tests."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.core.entities import (
    ConnectionType,
    JobStatus,
    JobType,
    Printer,
    PrinterStatus,
    PrintJob,
)
from src.utils.config import Config


@pytest.fixture
def sample_printer_data() -> dict[str, Any]:
    """Return sample printer data for testing.

    Returns:
        Dictionary with USB printer data.
    """
    return {
        "id": "test-printer-001",
        "name": "Test USB Printer",
        "connection_type": "usb",
        "vendor_id": 0x04B8,
        "product_id": 0x0202,
        "baudrate": 9600,
        "status": "disconnected",
    }


@pytest.fixture
def sample_serial_printer_data() -> dict[str, Any]:
    """Return sample serial printer data for testing.

    Returns:
        Dictionary with serial printer data.
    """
    return {
        "id": "test-printer-002",
        "name": "Test Serial Printer",
        "connection_type": "serial",
        "port": "/dev/ttyUSB0",
        "baudrate": 115200,
        "status": "disconnected",
    }


@pytest.fixture
def sample_print_job_data() -> dict[str, Any]:
    """Return sample print job data for testing.

    Returns:
        Dictionary with print job data.
    """
    return {
        "id": "test-job-001",
        "printer_id": "test-printer-001",
        "type": "text",
        "content": {"text": "Hello, World!"},
        "status": "pending",
    }


@pytest.fixture
def usb_printer(sample_printer_data: dict[str, Any]) -> Printer:
    """Create a USB Printer instance for testing.

    Args:
        sample_printer_data: Sample printer data.

    Returns:
        Printer instance configured for USB.
    """
    return Printer.from_dict(sample_printer_data)


@pytest.fixture
def serial_printer(sample_serial_printer_data: dict[str, Any]) -> Printer:
    """Create a Serial Printer instance for testing.

    Args:
        sample_serial_printer_data: Sample serial printer data.

    Returns:
        Printer instance configured for serial.
    """
    return Printer.from_dict(sample_serial_printer_data)


@pytest.fixture
def text_print_job(sample_print_job_data: dict[str, Any]) -> PrintJob:
    """Create a text PrintJob instance for testing.

    Args:
        sample_print_job_data: Sample job data.

    Returns:
        PrintJob instance for text printing.
    """
    return PrintJob.from_dict(sample_print_job_data)


@pytest.fixture
def barcode_print_job() -> PrintJob:
    """Create a barcode PrintJob instance for testing.

    Returns:
        PrintJob instance for barcode printing.
    """
    return PrintJob(
        printer_id="test-printer-001",
        type=JobType.BARCODE,
        content={"format": "CODE128", "data": "123456789"},
    )


@pytest.fixture
def qrcode_print_job() -> PrintJob:
    """Create a QR code PrintJob instance for testing.

    Returns:
        PrintJob instance for QR code printing.
    """
    return PrintJob(
        printer_id="test-printer-001",
        type=JobType.QRCODE,
        content={"data": "https://example.com"},
    )


@pytest.fixture
def image_print_job() -> PrintJob:
    """Create an image PrintJob instance for testing.

    Returns:
        PrintJob instance for image printing.
    """
    return PrintJob(
        printer_id="test-printer-001",
        type=JobType.IMAGE,
        content={"image_base64": "iVBORw0KGgoAAAANSUhEUg=="},
    )


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock Config instance for testing.

    Returns:
        MagicMock configured as a Config instance.
    """
    config = MagicMock(spec=Config)
    config.FLASK_ENV = "testing"
    config.FLASK_DEBUG = False
    config.API_HOST = "127.0.0.1"
    config.API_PORT = 5000
    config.DATABASE_PATH = Path("test.db")
    config.LOG_LEVEL = "DEBUG"
    config.DEFAULT_BAUDRATE = 9600
    config.DEFAULT_CONNECTION = "usb"
    config.API_KEY = "test-api-key"
    return config


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to temporary data directory.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_logs_dir(tmp_path: Path) -> Path:
    """Create a temporary logs directory for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to temporary logs directory.
    """
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture(autouse=True)
def reset_singletons() -> Generator[None, None, None]:
    """Reset any singleton state between tests.

    This fixture runs automatically before each test to ensure
    clean state.
    """
    import src.utils.config as config_module

    config_module._config = None
    yield
    config_module._config = None


@pytest.fixture
def connection_types() -> list[ConnectionType]:
    """Return all connection type enum values.

    Returns:
        List of ConnectionType enum values.
    """
    return list(ConnectionType)


@pytest.fixture
def printer_statuses() -> list[PrinterStatus]:
    """Return all printer status enum values.

    Returns:
        List of PrinterStatus enum values.
    """
    return list(PrinterStatus)


@pytest.fixture
def job_types() -> list[JobType]:
    """Return all job type enum values.

    Returns:
        List of JobType enum values.
    """
    return list(JobType)


@pytest.fixture
def job_statuses() -> list[JobStatus]:
    """Return all job status enum values.

    Returns:
        List of JobStatus enum values.
    """
    return list(JobStatus)

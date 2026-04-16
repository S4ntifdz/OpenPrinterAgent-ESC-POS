"""Unit tests for print service."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.entities import ConnectionType, JobStatus, JobType, Printer, PrinterStatus
from src.core.exceptions import JobError, PrinterError
from src.drivers.base import PrinterDriver
from src.models.database import Database
from src.services.job_service import JobService
from src.services.printer_service import PrinterService
from src.services.print_service import PrintService


class MockPrinterDriver(PrinterDriver):
    """Mock printer driver for testing."""

    def __init__(self, printer: Printer) -> None:
        super().__init__(printer)
        self._connected = True
        self._sent_data: list[bytes] = []

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, data: bytes) -> bool:
        self._sent_data.append(data)
        return True

    def status(self) -> dict[str, Any]:
        return {"connected": self._connected}

    def print_text(
        self,
        text: str,
        bold: bool = False,
        double_height: bool = False,
        double_width: bool = False,
    ) -> bool:
        return True

    def print_barcode(
        self,
        data: str,
        barcode_type: str = "CODE39",
        height: int = 50,
        width: int = 2,
    ) -> bool:
        return True

    def print_qrcode(
        self,
        data: str,
        size: int = 8,
        error_correction: str = "L",
    ) -> bool:
        return True

    def print_image(self, image_path: str, width: int = 512) -> bool:
        return True

    def cut_paper(self) -> bool:
        return True


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Create test database."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.init_schema()
    return db


@pytest.fixture
def printer_service(db: Database) -> PrinterService:
    """Create PrinterService instance."""
    return PrinterService(db)


@pytest.fixture
def job_service(db: Database) -> JobService:
    """Create JobService instance."""
    return JobService(db)


@pytest.fixture
def print_service(printer_service: PrinterService) -> PrintService:
    """Create PrintService instance."""
    return PrintService(printer_service, max_retries=3)


@pytest.fixture
def connected_printer(printer_service: PrinterService) -> Printer:
    """Create and connect a printer for testing."""
    printer = printer_service.add_printer(
        name="Test Printer",
        connection_type=ConnectionType.USB,
        vendor_id=0x04B8,
        product_id=0x0202,
    )

    with patch(
        "src.drivers.driver_factory.DriverFactory.create_driver",
        return_value=MockPrinterDriver(printer),
    ):
        printer_service.connect_printer(printer.id)

    return printer


class TestPrintServiceText:
    """Tests for PrintService text printing."""

    def test_print_text(self, print_service: PrintService, connected_printer: Printer) -> None:
        """Test printing text."""
        job = print_service.print_text(connected_printer.id, "Hello, World!")

        assert job.status == JobStatus.COMPLETED
        assert job.type == JobType.TEXT
        assert job.content["text"] == "Hello, World!"

    def test_print_text_bold(self, print_service: PrintService, connected_printer: Printer) -> None:
        """Test printing bold text."""
        job = print_service.print_text(connected_printer.id, "Bold Text", bold=True)

        assert job.content["bold"] is True

    def test_print_text_double_height(
        self, print_service: PrintService, connected_printer: Printer
    ) -> None:
        """Test printing double height text."""
        job = print_service.print_text(connected_printer.id, "Large Text", double_height=True)

        assert job.content["double_height"] is True

    def test_print_text_double_width(
        self, print_service: PrintService, connected_printer: Printer
    ) -> None:
        """Test printing double width text."""
        job = print_service.print_text(connected_printer.id, "Wide Text", double_width=True)

        assert job.content["double_width"] is True

    def test_print_text_not_connected(
        self, print_service: PrintService, printer_service: PrinterService
    ) -> None:
        """Test printing to non-connected printer raises error."""
        printer = printer_service.add_printer(
            name="Disconnected Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        with pytest.raises(PrinterError, match="Printer not connected"):
            print_service.print_text(printer.id, "Test")


class TestPrintServiceBarcode:
    """Tests for PrintService barcode printing."""

    def test_print_barcode(self, print_service: PrintService, connected_printer: Printer) -> None:
        """Test printing barcode."""
        job = print_service.print_barcode(connected_printer.id, "123456789", barcode_type="CODE128")

        assert job.status == JobStatus.COMPLETED
        assert job.type == JobType.BARCODE
        assert job.content["data"] == "123456789"
        assert job.content["barcode_type"] == "CODE128"

    def test_print_barcode_custom_dimensions(
        self, print_service: PrintService, connected_printer: Printer
    ) -> None:
        """Test printing barcode with custom dimensions."""
        job = print_service.print_barcode(connected_printer.id, "123456789", height=100, width=4)

        assert job.content["height"] == 100
        assert job.content["width"] == 4


class TestPrintServiceQRCode:
    """Tests for PrintService QR code printing."""

    def test_print_qrcode(self, print_service: PrintService, connected_printer: Printer) -> None:
        """Test printing QR code."""
        job = print_service.print_qrcode(connected_printer.id, "https://example.com")

        assert job.status == JobStatus.COMPLETED
        assert job.type == JobType.QRCODE
        assert job.content["data"] == "https://example.com"

    def test_print_qrcode_custom_size(
        self, print_service: PrintService, connected_printer: Printer
    ) -> None:
        """Test printing QR code with custom size."""
        job = print_service.print_qrcode(connected_printer.id, "data", size=12)

        assert job.content["size"] == 12

    def test_print_qrcode_error_correction(
        self, print_service: PrintService, connected_printer: Printer
    ) -> None:
        """Test printing QR code with error correction."""
        job = print_service.print_qrcode(connected_printer.id, "data", error_correction="H")

        assert job.content["error_correction"] == "H"


class TestPrintServiceRetry:
    """Tests for PrintService retry logic."""

    def test_print_retry_on_failure(
        self,
        print_service: PrintService,
        printer_service: PrinterService,
        connected_printer: Printer,
    ) -> None:
        """Test retry mechanism on print failure."""
        driver = printer_service.get_driver(connected_printer.id)
        call_count = 0

        def failing_print_text(
            text: str,
            bold: bool = False,
            double_height: bool = False,
            double_width: bool = False,
        ) -> bool:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return True

        with patch.object(driver, "print_text", side_effect=failing_print_text):
            job = print_service.print_text(connected_printer.id, "Test")

            assert job.status == JobStatus.COMPLETED
            assert call_count == 3

    def test_print_fails_after_max_retries(
        self,
        print_service: PrintService,
        printer_service: PrinterService,
        connected_printer: Printer,
    ) -> None:
        """Test job fails after max retries exhausted."""
        driver = printer_service.get_driver(connected_printer.id)

        with patch.object(driver, "send", side_effect=Exception("Permanent failure")):
            with patch.object(driver, "print_text", side_effect=Exception("Permanent failure")):
                with pytest.raises(JobError, match="Print failed after 3 attempts"):
                    print_service.print_text(connected_printer.id, "Test")


class TestPrintServiceDriverInteraction:
    """Tests for PrintService driver interaction."""

    def test_print_calls_driver_methods(
        self,
        print_service: PrintService,
        printer_service: PrinterService,
        connected_printer: Printer,
    ) -> None:
        """Test print service calls correct driver methods."""
        driver = printer_service.get_driver(connected_printer.id)

        with patch.object(driver, "print_text") as mock_print:
            with patch.object(driver, "cut_paper") as mock_cut:
                print_service.print_text(connected_printer.id, "Test")

                mock_print.assert_called_once()
                mock_cut.assert_called_once()

    def test_print_barcode_calls_driver(
        self,
        print_service: PrintService,
        printer_service: PrinterService,
        connected_printer: Printer,
    ) -> None:
        """Test barcode printing calls driver methods."""
        driver = printer_service.get_driver(connected_printer.id)

        with patch.object(driver, "print_barcode") as mock_barcode:
            with patch.object(driver, "cut_paper"):
                print_service.print_barcode(connected_printer.id, "12345")

                mock_barcode.assert_called_once()

    def test_print_qrcode_calls_driver(
        self,
        print_service: PrintService,
        printer_service: PrinterService,
        connected_printer: Printer,
    ) -> None:
        """Test QR code printing calls driver methods."""
        driver = printer_service.get_driver(connected_printer.id)

        with patch.object(driver, "print_qrcode") as mock_qr:
            with patch.object(driver, "cut_paper"):
                print_service.print_qrcode(connected_printer.id, "data")

                mock_qr.assert_called_once()

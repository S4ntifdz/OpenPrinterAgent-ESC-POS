"""Unit tests for printer service."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.entities import ConnectionType, Printer, PrinterStatus
from src.core.exceptions import PrinterError
from src.drivers.base import PrinterDriver
from src.models.database import Database
from src.services.printer_service import PrinterService


class MockPrinterDriver(PrinterDriver):
    """Mock printer driver for testing."""

    def __init__(self, printer: Printer) -> None:
        super().__init__(printer)
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, data: bytes) -> bool:
        return True

    def status(self) -> dict[str, Any]:
        return {"connected": self._connected}


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


class TestPrinterService:
    """Tests for PrinterService class."""

    def test_add_printer_usb(self, printer_service: PrinterService) -> None:
        """Test adding USB printer."""
        printer = printer_service.add_printer(
            name="Test USB Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        assert printer.name == "Test USB Printer"
        assert printer.connection_type == ConnectionType.USB
        assert printer.vendor_id == 0x04B8
        assert printer.product_id == 0x0202
        assert printer.status == PrinterStatus.DISCONNECTED

    def test_add_printer_serial(self, printer_service: PrinterService) -> None:
        """Test adding Serial printer."""
        printer = printer_service.add_printer(
            name="Test Serial Printer",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=115200,
        )

        assert printer.name == "Test Serial Printer"
        assert printer.connection_type == ConnectionType.SERIAL
        assert printer.port == "/dev/ttyUSB0"
        assert printer.baudrate == 115200

    def test_get_printer(self, printer_service: PrinterService) -> None:
        """Test getting printer by ID."""
        created = printer_service.add_printer(
            name="Test Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        retrieved = printer_service.get_printer(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_printer_not_found(self, printer_service: PrinterService) -> None:
        """Test getting non-existent printer."""
        result = printer_service.get_printer("non-existent-id")
        assert result is None

    def test_list_printers(self, printer_service: PrinterService, db: Database) -> None:
        """Test listing all printers."""
        db.init_schema()

        printer_service.add_printer(
            name="Printer 1",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        printer_service.add_printer(
            name="Printer 2",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
        )

        printers = printer_service.list_printers()

        assert len(printers) == 2

    def test_list_printers_empty(self, printer_service: PrinterService) -> None:
        """Test listing printers when none exist."""
        printers = printer_service.list_printers()
        assert len(printers) == 0

    def test_remove_printer(self, printer_service: PrinterService) -> None:
        """Test removing a printer."""
        printer = printer_service.add_printer(
            name="Test Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        result = printer_service.remove_printer(printer.id)

        assert result is True
        assert printer_service.get_printer(printer.id) is None

    def test_remove_printer_not_found(self, printer_service: PrinterService) -> None:
        """Test removing non-existent printer."""
        result = printer_service.remove_printer("non-existent-id")
        assert result is True

    def test_remove_printer_disconnects_first(self, printer_service: PrinterService) -> None:
        """Test removing connected printer disconnects first."""
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
            printer_service.remove_printer(printer.id)

        assert printer_service.get_driver(printer.id) is None


class TestPrinterServiceConnection:
    """Tests for PrinterService connection management."""

    def test_connect_printer(self, printer_service: PrinterService) -> None:
        """Test connecting a printer."""
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
            result = printer_service.connect_printer(printer.id)

        assert result.status == PrinterStatus.CONNECTED
        assert printer_service.get_driver(printer.id) is not None

    def test_connect_printer_not_found(self, printer_service: PrinterService) -> None:
        """Test connecting non-existent printer raises error."""
        with pytest.raises(PrinterError, match="Printer not found"):
            printer_service.connect_printer("non-existent-id")

    def test_connect_printer_failure(self, printer_service: PrinterService) -> None:
        """Test connecting printer handles failure."""
        printer = printer_service.add_printer(
            name="Test Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        with patch("src.drivers.driver_factory.DriverFactory.create_driver") as mock_factory:
            from src.core.exceptions import DriverError

            mock_factory.side_effect = DriverError("Connection failed")

            with pytest.raises(PrinterError, match="Connection failed"):
                printer_service.connect_printer(printer.id)

    def test_disconnect_printer(self, printer_service: PrinterService) -> None:
        """Test disconnecting a printer."""
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
            result = printer_service.disconnect_printer(printer.id)

        assert result.status == PrinterStatus.DISCONNECTED
        assert printer_service.get_driver(printer.id) is None

    def test_disconnect_printer_not_found(self, printer_service: PrinterService) -> None:
        """Test disconnecting non-existent printer raises error."""
        with pytest.raises(PrinterError, match="Printer not found"):
            printer_service.disconnect_printer("non-existent-id")

    def test_disconnect_not_connected_printer(self, printer_service: PrinterService) -> None:
        """Test disconnecting printer that is not connected."""
        printer = printer_service.add_printer(
            name="Test Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        result = printer_service.disconnect_printer(printer.id)

        assert result.status == PrinterStatus.DISCONNECTED

    def test_get_driver_not_connected(self, printer_service: PrinterService) -> None:
        """Test getting driver for non-connected printer."""
        printer = printer_service.add_printer(
            name="Test Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )

        driver = printer_service.get_driver(printer.id)
        assert driver is None

    def test_get_driver_connected(self, printer_service: PrinterService) -> None:
        """Test getting driver for connected printer."""
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
            driver = printer_service.get_driver(printer.id)

        assert driver is not None
        assert isinstance(driver, MockPrinterDriver)

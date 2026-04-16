"""Unit tests for driver components."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.entities import ConnectionType, Printer
from src.core.exceptions import DriverError
from src.drivers.base import PrinterDriver
from src.drivers.driver_factory import DriverFactory


class MockPrinterDriver(PrinterDriver):
    """Mock implementation of PrinterDriver for testing."""

    def __init__(self, printer: Printer) -> None:
        super().__init__(printer)

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def send(self, data: bytes) -> bool:
        return True

    def status(self) -> dict[str, Any]:
        return {"connected": self._connected}


class TestPrinterDriverInterface:
    """Tests for PrinterDriver abstract base class."""

    def test_is_abstract(self) -> None:
        """Test that PrinterDriver cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            PrinterDriver.__new__(PrinterDriver)

    def test_subclass_can_be_instantiated(self) -> None:
        """Test that subclasses can be instantiated."""
        printer = Printer(
            name="Test",
            connection_type=ConnectionType.USB,
            vendor_id=0x1234,
            product_id=0x5678,
        )
        driver = MockPrinterDriver(printer)
        assert driver is not None

    def test_printer_property(self) -> None:
        """Test printer property returns associated printer."""
        printer = Printer(
            name="Test",
            connection_type=ConnectionType.USB,
            vendor_id=0x1234,
            product_id=0x5678,
        )
        driver = MockPrinterDriver(printer)
        assert driver.printer.name == "Test"

    def test_is_connected_property(self) -> None:
        """Test is_connected property."""
        printer = Printer(
            name="Test",
            connection_type=ConnectionType.USB,
            vendor_id=0x1234,
            product_id=0x5678,
        )
        driver = MockPrinterDriver(printer)
        assert driver.is_connected is False
        driver.connect()
        assert driver.is_connected is True
        driver.disconnect()
        assert driver.is_connected is False

    def test_repr(self) -> None:
        """Test string representation."""
        printer = Printer(
            name="Test",
            connection_type=ConnectionType.USB,
            vendor_id=0x1234,
            product_id=0x5678,
        )
        driver = MockPrinterDriver(printer)
        repr_str = repr(driver)
        assert "MockPrinterDriver" in repr_str
        assert "Test" in repr_str


class TestDriverFactory:
    """Tests for DriverFactory."""

    def test_create_usb_driver(self) -> None:
        """Test creating USB driver via factory."""
        printer = Printer(
            name="USB Printer",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        from src.drivers.usb_driver import USBDriver

        driver = DriverFactory.create_driver(printer)
        assert isinstance(driver, USBDriver)

    def test_create_serial_driver(self) -> None:
        """Test creating Serial driver via factory."""
        printer = Printer(
            name="Serial Printer",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        from src.drivers.serial_driver import SerialDriver

        driver = DriverFactory.create_driver(printer)
        assert isinstance(driver, SerialDriver)

    def test_unsupported_connection_type(self) -> None:
        """Test factory raises error for unsupported type."""
        printer = MagicMock(spec=Printer)
        printer.connection_type = MagicMock()
        printer.connection_type.value = "network"

        with pytest.raises(DriverError, match="Unsupported connection type"):
            DriverFactory.create_driver(printer)

    def test_get_supported_types(self) -> None:
        """Test getting list of supported connection types."""
        types = DriverFactory.get_supported_types()
        assert "usb" in types
        assert "serial" in types
        assert len(types) == 2


class TestUSBDriver:
    """Tests for USBDriver class."""

    def test_requires_usb_connection_type(self) -> None:
        """Test USBDriver raises error for non-USB connection."""
        from src.drivers.usb_driver import USBDriver

        serial_printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
        )
        with pytest.raises(DriverError, match="USB connection type"):
            USBDriver(printer=serial_printer)

    def test_initial_state_not_connected(self) -> None:
        """Test driver starts in disconnected state."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)
        assert driver.is_connected is False

    def test_status_returns_connection_info(self) -> None:
        """Test status method returns correct info."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)
        status = driver.status()

        assert status["connection_type"] == "usb"
        assert status["vendor_id"] == 0x04B8
        assert status["product_id"] == 0x0202
        assert status["connected"] is False

    def test_repr(self) -> None:
        """Test string representation."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)
        repr_str = repr(driver)

        assert "USBDriver" in repr_str
        assert "0x04B8" in repr_str
        assert "0x0202" in repr_str


class TestSerialDriver:
    """Tests for SerialDriver class."""

    def test_requires_serial_connection_type(self) -> None:
        """Test SerialDriver raises error for non-Serial connection."""
        from src.drivers.serial_driver import SerialDriver

        usb_printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        with pytest.raises(DriverError, match="Serial connection type"):
            SerialDriver(printer=usb_printer)

    def test_initial_state_not_connected(self) -> None:
        """Test driver starts in disconnected state."""
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
        )
        driver = SerialDriver(printer=printer)
        assert driver.is_connected is False

    def test_status_returns_connection_info(self) -> None:
        """Test status method returns correct info."""
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=115200,
        )
        driver = SerialDriver(printer=printer)
        status = driver.status()

        assert status["connection_type"] == "serial"
        assert status["port"] == "/dev/ttyUSB0"
        assert status["baudrate"] == 115200
        assert status["connected"] is False

    def test_repr(self) -> None:
        """Test string representation."""
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        driver = SerialDriver(printer=printer)
        repr_str = repr(driver)

        assert "SerialDriver" in repr_str
        assert "/dev/ttyUSB0" in repr_str
        assert "9600" in repr_str


class TestUSBDriverWithMocks:
    """Tests for USBDriver with mocked USB library."""

    def test_connect_success(self) -> None:
        """Test successful USB connection."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)

        mock_device = MagicMock()
        with patch("usb.core.find", return_value=mock_device):
            result = driver.connect()
            assert result is True
            assert driver.is_connected is True

    def test_connect_device_not_found(self) -> None:
        """Test USB connection when device not found."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0xFFFF,
            product_id=0xFFFF,
        )
        driver = USBDriver(printer=printer)

        with patch("usb.core.find", return_value=None):
            result = driver.connect()
            assert result is False
            assert driver.is_connected is False

    def test_disconnect(self) -> None:
        """Test USB disconnect."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)

        mock_device = MagicMock()
        with patch("usb.core.find", return_value=mock_device):
            driver.connect()
            assert driver.is_connected is True

        driver.disconnect()
        assert driver.is_connected is False

    def test_send_success(self) -> None:
        """Test successful data send."""
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)

        mock_device = MagicMock()
        with patch("usb.core.find", return_value=mock_device):
            driver.connect()
            result = driver.send(b"test data")
            assert result is True

    def test_send_not_connected(self) -> None:
        """Test send when not connected raises error."""
        from src.core.exceptions import ConnectionError
        from src.drivers.usb_driver import USBDriver

        printer = Printer(
            name="USB",
            connection_type=ConnectionType.USB,
            vendor_id=0x04B8,
            product_id=0x0202,
        )
        driver = USBDriver(printer=printer)

        with pytest.raises(ConnectionError, match="Not connected"):
            driver.send(b"test data")


class TestSerialDriverWithMocks:
    """Tests for SerialDriver with mocked pyserial library."""

    def test_connect_success(self) -> None:
        """Test successful Serial connection."""
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        driver = SerialDriver(printer=printer)

        mock_serial = MagicMock()
        with patch("serial.Serial", return_value=mock_serial):
            result = driver.connect()
            assert result is True
            assert driver.is_connected is True

    def test_disconnect(self) -> None:
        """Test Serial disconnect."""
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        driver = SerialDriver(printer=printer)

        mock_serial = MagicMock()
        with patch("serial.Serial", return_value=mock_serial):
            driver.connect()
            assert driver.is_connected is True

        driver.disconnect()
        assert driver.is_connected is False

    def test_send_success(self) -> None:
        """Test successful data send."""
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        driver = SerialDriver(printer=printer)

        mock_serial = MagicMock()
        with patch("serial.Serial", return_value=mock_serial):
            driver.connect()
            result = driver.send(b"test data")
            assert result is True
            mock_serial.write.assert_called_once_with(b"test data")

    def test_send_not_connected(self) -> None:
        """Test send when not connected raises error."""
        from src.core.exceptions import ConnectionError
        from src.drivers.serial_driver import SerialDriver

        printer = Printer(
            name="Serial",
            connection_type=ConnectionType.SERIAL,
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        driver = SerialDriver(printer=printer)

        with pytest.raises(ConnectionError, match="Not connected"):
            driver.send(b"test data")

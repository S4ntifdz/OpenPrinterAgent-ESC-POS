"""Serial driver implementation using PySerial.

This module provides the SerialDriver class that implements the PrinterDriver
interface for serial-connected ESC/POS thermal printers using the pyserial library.
"""

from typing import Any

from src.core.entities import Printer
from src.core.exceptions import ConnectionError, DriverError
from src.drivers.base import PrinterDriver


class SerialDriver(PrinterDriver):
    """Driver for Serial-connected printers using PySerial.

    This driver handles communication with printers connected via
    RS232 serial port using the pyserial library.

    Attributes:
        port: Serial port path (e.g., /dev/ttyUSB0 or COM1).
        baudrate: Serial baud rate (default: 9600).
    """

    def __init__(self, printer: Printer) -> None:
        """Initialize Serial driver with printer configuration.

        Args:
            printer: Printer entity with Serial connection details.

        Raises:
            DriverError: If printer configuration is invalid.
        """
        if printer.connection_type.value != "serial":
            msg = "SerialDriver requires Serial connection type"
            raise DriverError(msg)

        super().__init__(printer)
        self._port = printer.port
        self._baudrate = printer.baudrate
        self._serial: Any = None

    def connect(self) -> bool:
        """Connect to the Serial printer.

        Attempts to open and configure the serial port.

        Returns:
            True if connection successful.

        Raises:
            ConnectionError: If serial port cannot be opened.
        """
        try:
            import serial

            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=5,
                write_timeout=5,
            )
            self._connected = True
            return True

        except ImportError as e:
            msg = f"pyserial library not available: {e}"
            raise ConnectionError(msg) from e
        except serial.serialutil.SerialException as e:
            self._connected = False
            msg = f"Failed to connect to serial port {self._port}: {e}"
            raise ConnectionError(msg) from e

    def disconnect(self) -> None:
        """Disconnect from the Serial printer.

        Closes the serial port and releases resources.
        """
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            finally:
                self._serial = None
                self._connected = False

    def send(self, data: bytes) -> bool:
        """Send raw data to the Serial printer.

        Args:
            data: Raw bytes to send (ESC/POS commands).

        Returns:
            True if send successful.

        Raises:
            ConnectionError: If not connected or port closed.
            DriverError: If serial write operation fails.
        """
        if not self._connected or self._serial is None:
            msg = "Not connected to printer"
            raise ConnectionError(msg)

        try:
            self._serial.write(data)
            self._serial.flush()
            return True

        except Exception as e:
            msg = f"Failed to send data: {e}"
            raise DriverError(msg) from e

    def status(self) -> dict[str, Any]:
        """Get printer status via Serial.

        Returns:
            Dictionary with printer status information.
        """
        return {
            "connected": self._connected,
            "connection_type": "serial",
            "port": self._port,
            "baudrate": self._baudrate,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SerialDriver("
            f"port={self._port!r}, "
            f"baudrate={self._baudrate}, "
            f"connected={self._connected})"
        )

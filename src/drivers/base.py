"""Base abstract driver interface for OpenPrinterAgent.

This module defines the abstract base class that all printer drivers
must implement, ensuring a consistent interface regardless of the
underlying communication method (USB, Serial, Network, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any

from src.core.entities import Printer


class PrinterDriver(ABC):
    """Abstract base class for all printer drivers.

    This class defines the interface that all printer drivers must implement.
    It provides the contract for connecting, disconnecting, sending data,
    and checking status.

    Attributes:
        printer: The Printer entity this driver is connected to.
    """

    def __init__(self, printer: Printer) -> None:
        """Initialize the driver with a printer entity.

        Args:
            printer: The Printer entity to associate with this driver.
        """
        self._printer = printer
        self._connected = False

    @property
    def printer(self) -> Printer:
        """Get the printer associated with this driver.

        Returns:
            The Printer entity.
        """
        return self._printer

    @property
    def is_connected(self) -> bool:
        """Check if the driver is currently connected.

        Returns:
            True if connected, False otherwise.
        """
        return self._connected

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the printer.

        Establishes communication with the physical or virtual printer.
        This method should handle device detection, initialization,
        and any handshaking required.

        Returns:
            True if connection successful, False otherwise.

        Raises:
            DriverError: If connection fails critically.
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the printer.

        Closes the communication channel and releases any resources.
        This method should be idempotent - calling it multiple times
        should not raise errors.
        """
        ...

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Send raw bytes to the printer.

        Sends the given byte data to the printer. The data should already
        be in the format expected by the printer (ESC/POS commands,
        image data, etc.).

        Args:
            data: Raw bytes to send to the printer.

        Returns:
            True if send successful, False otherwise.

        Raises:
            DriverError: If send operation fails critically.
        """
        ...

    @abstractmethod
    def status(self) -> dict[str, Any]:
        """Get the current status of the printer.

        Returns a dictionary with status information from the printer.
        The exact fields depend on the printer capabilities but typically
        include paper status, error states, etc.

        Returns:
            Dictionary with status information.
        """
        ...

    def __repr__(self) -> str:
        """Return string representation of the driver.

        Returns:
            String representation.
        """
        return (
            f"{self.__class__.__name__}("
            f"printer={self._printer.name!r}, "
            f"connected={self._connected})"
        )

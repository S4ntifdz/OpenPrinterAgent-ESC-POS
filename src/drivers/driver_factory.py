"""Factory for creating printer drivers based on connection type.

This module implements the Factory Pattern to create the appropriate
driver instance based on the printer's connection configuration.
"""

from src.core.entities import ConnectionType, Printer
from src.core.exceptions import DriverError
from src.drivers.base import PrinterDriver


class DriverFactory:
    """Factory class for creating printer driver instances.

    This factory inspects the Printer entity's connection_type and
    returns the appropriate driver implementation.
    """

    @staticmethod
    def create_driver(printer: Printer) -> PrinterDriver:
        """Create a driver instance for the given printer.

        This method acts as a factory, selecting the appropriate driver
        based on the printer's connection configuration (USB, Serial, etc.).

        Args:
            printer: The Printer entity to create a driver for.

        Returns:
            A PrinterDriver instance appropriate for the printer's connection.

        Raises:
            DriverError: If connection_type is not supported or driver
                        cannot be created.
        """
        if printer.connection_type == ConnectionType.USB:
            from src.drivers.usb_driver import USBDriver

            return USBDriver(printer=printer)

        if printer.connection_type == ConnectionType.SERIAL:
            from src.drivers.serial_driver import SerialDriver

            return SerialDriver(printer=printer)

        msg = f"Unsupported connection type: {printer.connection_type.value}"
        raise DriverError(msg)

    @staticmethod
    def get_supported_types() -> list[str]:
        """Get list of supported connection types.

        Returns:
            List of supported connection type values as strings.
        """
        return [ct.value for ct in ConnectionType]

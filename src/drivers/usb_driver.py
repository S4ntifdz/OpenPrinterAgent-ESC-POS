"""USB driver implementation using PyUSB.

This module provides the USBDriver class that implements the PrinterDriver
interface for USB-connected ESC/POS thermal printers using the pyusb library.
"""

from typing import Any

from src.core.entities import Printer
from src.core.exceptions import ConnectionError, DriverError
from src.drivers.base import PrinterDriver
from src.utils.logging import get_logger

logger = get_logger(__name__)


class USBDriver(PrinterDriver):
    """Driver for USB-connected printers using PyUSB.

    This driver handles communication with printers connected via USB
    using the pyusb library and libusb backend.

    Attributes:
        vendor_id: USB vendor ID of the printer.
        product_id: USB product ID of the printer.
    """

    def __init__(self, printer: Printer) -> None:
        """Initialize USB driver with printer configuration.

        Args:
            printer: Printer entity with USB connection details.

        Raises:
            DriverError: If printer configuration is invalid.
        """
        if printer.connection_type.value != "usb":
            msg = "USBDriver requires USB connection type"
            raise DriverError(msg)

        super().__init__(printer)
        self._vendor_id = printer.vendor_id
        self._product_id = printer.product_id
        self._device: Any = None

    def connect(self) -> bool:
        """Connect to the USB printer.

        Attempts to find and open the USB device based on vendor_id
        and product_id.

        Returns:
            True if connection successful.

        Raises:
            ConnectionError: If USB device cannot be found or opened.
        """
        try:
            import usb.core
            import usb.util

            self._device = usb.core.find(idVendor=self._vendor_id, idProduct=self._product_id)

            if self._device is None:
                self._connected = False
                return False

            # On Linux, detaching can fail if we don't have permissions or it's already detached
            try:
                if self._device.is_kernel_driver_active(0):
                    logger.info(f"Detaching kernel driver for printer {self._vendor_id:04x}:{self._product_id:04x}")
                    self._device.detach_kernel_driver(0)
            except (usb.core.USBError, NotImplementedError) as e:
                logger.debug(f"Kernel detachment skipped/failed: {e}")

            # set_configuration() can fail if another process has the device open.
            # On Linux, if it's already configured, we can often just proceed.
            try:
                self._device.set_configuration()
            except usb.core.USBError as e:
                if e.errno == 16: # Resource busy
                    logger.warning("USB device busy during set_configuration, attempting to proceed...")
                else:
                    raise

            # Find the OUT endpoint dynamically
            cfg = self._device.get_active_configuration()
            intf = cfg[(0,0)]

            import usb.util
            self._endpoint = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT
            )

            if self._endpoint is None:
                raise ConnectionError("Could not find OUT endpoint on USB device")

            logger.info(f"Found USB OUT endpoint: 0x{self._endpoint.bEndpointAddress:02x}")

            try:
                usb.util.claim_interface(self._device, 0)
            except usb.core.USBError as e:
                if e.errno == 16: # Resource busy
                    logger.warning("Interface 0 already claimed or busy, attempting to proceed anyway.")
                else:
                    raise

            self._connected = True
            return True

        except ImportError as e:
            msg = f"pyusb library not available: {e}"
            raise ConnectionError(msg) from e
        except usb.core.USBError as e:
            self._connected = False
            msg = f"Failed to connect to USB device: {e}"
            raise ConnectionError(msg) from e

    def print_text(self, *args: Any, **kwargs: Any) -> None:
        """Safety fallback for legacy calls (should not be needed)."""
        logger.error("Legacy print_text called on USBDriver. This should not happen.")


    def disconnect(self) -> None:
        """Disconnect from the USB printer.

        Releases the interface and resets the device handle.
        """
        if self._device:
            try:
                import usb.util
                usb.util.release_interface(self._device, 0)
                # Re-attach kernel driver if possible
                try:
                    self._device.attach_kernel_driver(0)
                except:
                    pass
            except:
                pass
            self._device = None
            self._endpoint = None
        
        self._connected = False

    def send(self, data: bytes) -> bool:
        """Send raw bytes to the USB printer.

        Args:
            data: Raw ESC/POS bytes to send.

        Returns:
            True if send successful, False otherwise.

        Raises:
            DriverError: If sending data fails critically.
        """
        if not self._connected or self._device is None or self._endpoint is None:
            if not self.connect():
                return False

        try:
            # Use the dynamically discovered endpoint
            self._device.write(self._endpoint.bEndpointAddress, data, timeout=5000)
            return True
        except Exception as e:
            logger.error(f"USB send failed: {e}")
            self._connected = False
            return False

    def status(self) -> dict[str, Any]:
        """Get printer status via USB.

        Returns:
            Dictionary with printer status information.
        """
        return {
            "connected": self._connected,
            "connection_type": "usb",
            "vendor_id": self._vendor_id,
            "product_id": self._product_id,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"USBDriver("
            f"vendor=0x{self._vendor_id:04X}, "
            f"product=0x{self._product_id:04X}, "
            f"connected={self._connected})"
        )

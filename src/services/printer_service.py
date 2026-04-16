"""Printer management service for OpenPrinterAgent.

This module provides the PrinterService class that handles the business
logic for managing printers: adding, removing, listing, connecting, and disconnecting.
"""

from typing import Any

from src.core.entities import ConnectionType, Printer, PrinterStatus
from src.core.exceptions import DriverError, PrinterError
from src.drivers.base import PrinterDriver
from src.drivers.driver_factory import DriverFactory
from src.models.database import Database
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PrinterService:
    """Service for managing printers.

    This service provides business logic for printer management operations
    including CRUD operations and connection management.

    Attributes:
        database: Database instance for persistence.
    """

    def __init__(self, database: Database) -> None:
        """Initialize printer service.

        Args:
            database: Database instance for persistence.
        """
        self._db = database
        self._drivers: dict[str, PrinterDriver] = {}

    def add_printer(
        self,
        name: str,
        connection_type: ConnectionType,
        vendor_id: int | None = None,
        product_id: int | None = None,
        port: str | None = None,
        baudrate: int = 9600,
    ) -> Printer:
        """Add a new printer.

        Args:
            name: Human-readable name for the printer.
            connection_type: USB or Serial connection.
            vendor_id: USB vendor ID (required for USB).
            product_id: USB product ID (required for USB).
            port: Serial port path (required for Serial).
            baudrate: Serial baud rate (default: 9600).

        Returns:
            The created Printer entity.

        Raises:
            PrinterError: If validation fails or printer already exists.
        """

        printer = Printer(
            name=name,
            connection_type=connection_type,
            vendor_id=vendor_id,
            product_id=product_id,
            port=port,
            baudrate=baudrate,
            status=PrinterStatus.DISCONNECTED,
        )

        query = """
        INSERT INTO printers (id, name, connection_type, vendor_id, product_id, port, baudrate, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self._db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    printer.id,
                    printer.name,
                    printer.connection_type.value,
                    printer.vendor_id,
                    printer.product_id,
                    printer.port,
                    printer.baudrate,
                    printer.status.value,
                    printer.created_at.isoformat(),
                    printer.updated_at.isoformat(),
                ),
            )

        logger.info(f"Printer added: {printer.name} ({printer.id})")
        return printer

    def remove_printer(self, printer_id: str) -> bool:
        """Remove a printer.

        Args:
            printer_id: ID of the printer to remove.

        Returns:
            True if printer was removed.

        Raises:
            PrinterError: If printer not found or has active driver.
        """
        if printer_id in self._drivers:
            self.disconnect_printer(printer_id)

        query = "DELETE FROM printers WHERE id = ?"

        with self._db.get_cursor() as cursor:
            cursor.execute(query, (printer_id,))

        logger.info(f"Printer removed: {printer_id}")
        return True

    def get_printer(self, printer_id: str) -> Printer | None:
        """Get a printer by ID.

        Args:
            printer_id: ID of the printer.

        Returns:
            Printer entity or None if not found.
        """
        query = "SELECT * FROM printers WHERE id = ?"

        with self._db.get_cursor() as cursor:
            cursor.execute(query, (printer_id,))
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_printer(row)

    def list_printers(self) -> list[Printer]:
        """List all printers.

        Returns:
            List of Printer entities.
        """
        query = "SELECT * FROM printers ORDER BY created_at DESC"

        with self._db.get_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [self._row_to_printer(row) for row in rows]

    def connect_printer(self, printer_id: str) -> Printer:
        """Connect to a printer.

        Uses the DriverFactory to create the appropriate driver and
        attempts to establish a connection.

        Args:
            printer_id: ID of the printer to connect.

        Returns:
            Updated Printer entity with CONNECTED status.

        Raises:
            PrinterError: If printer not found or connection fails.
        """
        printer = self.get_printer(printer_id)
        if printer is None:
            msg = f"Printer not found: {printer_id}"
            raise PrinterError(msg)

        try:
            driver = DriverFactory.create_driver(printer)
            driver.connect()
            self._drivers[printer_id] = driver

            printer.status = PrinterStatus.CONNECTED
            self._update_printer_status(printer_id, PrinterStatus.CONNECTED)

            logger.info(f"Printer connected: {printer.name}")
            return printer

        except DriverError as e:
            logger.error(f"Failed to connect printer {printer_id}: {e}")
            raise PrinterError(f"Connection failed: {e}") from e

    def disconnect_printer(self, printer_id: str) -> Printer:
        """Disconnect a printer.

        Args:
            printer_id: ID of the printer to disconnect.

        Returns:
            Updated Printer entity with DISCONNECTED status.

        Raises:
            PrinterError: If printer not found or not connected.
        """
        printer = self.get_printer(printer_id)
        if printer is None:
            msg = f"Printer not found: {printer_id}"
            raise PrinterError(msg)

        if printer_id in self._drivers:
            driver = self._drivers.pop(printer_id)
            driver.disconnect()

        printer.status = PrinterStatus.DISCONNECTED
        self._update_printer_status(printer_id, PrinterStatus.DISCONNECTED)

        logger.info(f"Printer disconnected: {printer.name}")
        return printer

    def get_driver(self, printer_id: str) -> PrinterDriver | None:
        """Get the driver for a printer.

        Args:
            printer_id: ID of the printer.

        Returns:
            PrinterDriver instance or None if not connected.
        """
        return self._drivers.get(printer_id)

    def _update_printer_status(self, printer_id: str, status: PrinterStatus) -> None:
        """Update printer status in database.

        Args:
            printer_id: ID of the printer.
            status: New status.
        """
        from datetime import datetime, timezone

        query = """
        UPDATE printers SET status = ?, updated_at = ? WHERE id = ?
        """

        with self._db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    status.value,
                    datetime.now(timezone.utc).isoformat(),
                    printer_id,
                ),
            )

    def _row_to_printer(self, row: Any) -> Printer:
        """Convert database row to Printer entity.

        Args:
            row: Database row.

        Returns:
            Printer entity.
        """
        return Printer(
            id=row["id"],
            name=row["name"],
            connection_type=ConnectionType(row["connection_type"]),
            vendor_id=row["vendor_id"],
            product_id=row["product_id"],
            port=row["port"],
            baudrate=row["baudrate"],
            status=PrinterStatus(row["status"]),
        )

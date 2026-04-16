"""Print service for OpenPrinterAgent.

This module provides the PrintService class that handles sending
print jobs to printers using the ESCPOS protocol.
"""

from typing import Any

from src.core.entities import JobType, PrintJob
from src.core.exceptions import JobError, PrinterError
from src.drivers.base import PrinterDriver
from src.drivers.escpos_protocol import ESCPOSProtocol
from src.services.printer_service import PrinterService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PrintService:
    """Service for printing operations.

    This service handles sending print jobs to printers using
    the ESCPOS protocol and manages the print queue.

    Attributes:
        printer_service: PrinterService instance for printer management.
        max_retries: Maximum number of retry attempts for failed prints.
    """

    def __init__(self, printer_service: PrinterService, max_retries: int = 3) -> None:
        """Initialize print service.

        Args:
            printer_service: PrinterService instance for printer management.
            max_retries: Maximum number of retry attempts (default: 3).
        """
        self._printer_service = printer_service
        self._max_retries = max_retries
        self._escpos = ESCPOSProtocol()

    def print_text(
        self,
        printer_id: str,
        text: str,
        bold: bool = False,
        double_height: bool = False,
        double_width: bool = False,
    ) -> PrintJob:
        """Print text content.

        Args:
            printer_id: ID of the printer to use.
            text: Text content to print.
            bold: Enable bold text.
            double_height: Enable double height.
            double_width: Enable double width.

        Returns:
            PrintJob entity with updated status.

        Raises:
            PrinterError: If printer not found or not connected.
            JobError: If printing fails.
        """
        content = {
            "text": text,
            "bold": bold,
            "double_height": double_height,
            "double_width": double_width,
        }
        return self._send_print_job(printer_id, JobType.TEXT, content)

    def print_barcode(
        self,
        printer_id: str,
        data: str,
        barcode_type: str = "CODE39",
        height: int = 50,
        width: int = 2,
    ) -> PrintJob:
        """Print barcode.

        Args:
            printer_id: ID of the printer to use.
            data: Data to encode in barcode.
            barcode_type: Barcode type (CODE39, CODE128, EAN13, etc).
            height: Barcode height.
            width: Barcode width.

        Returns:
            PrintJob entity with updated status.

        Raises:
            PrinterError: If printer not found or not connected.
            JobError: If printing fails.
        """
        content = {
            "data": data,
            "barcode_type": barcode_type,
            "height": height,
            "width": width,
        }
        return self._send_print_job(printer_id, JobType.BARCODE, content)

    def print_qrcode(
        self,
        printer_id: str,
        data: str,
        size: int = 8,
        error_correction: str = "L",
    ) -> PrintJob:
        """Print QR code.

        Args:
            printer_id: ID of the printer to use.
            data: Data to encode in QR code.
            size: QR code size (3-15).
            error_correction: Error correction level (L, M, Q, H).

        Returns:
            PrintJob entity with updated status.

        Raises:
            PrinterError: If printer not found or not connected.
            JobError: If printing fails.
        """
        content = {
            "data": data,
            "size": size,
            "error_correction": error_correction,
        }
        return self._send_print_job(printer_id, JobType.QRCODE, content)

    def print_image(
        self,
        printer_id: str,
        image_path: str,
        width: int = 512,
    ) -> PrintJob:
        """Print image.

        Args:
            printer_id: ID of the printer to use.
            image_path: Path to the image file.
            width: Target width in pixels.

        Returns:
            PrintJob entity with updated status.

        Raises:
            PrinterError: If printer not found or not connected.
            JobError: If printing fails.
        """
        content = {
            "image_path": image_path,
            "width": width,
        }
        return self._send_print_job(printer_id, JobType.IMAGE, content)

    def _send_print_job(
        self,
        printer_id: str,
        job_type: JobType,
        content: dict[str, Any],
    ) -> PrintJob:
        """Send a print job to a printer.

        Args:
            printer_id: ID of the printer to use.
            job_type: Type of print job.
            content: Job content data.

        Returns:
            PrintJob entity with updated status.

        Raises:
            PrinterError: If printer not found or not connected.
            JobError: If printing fails after all retries.
        """
        driver = self._printer_service.get_driver(printer_id)
        if driver is None:
            msg = f"Printer not connected: {printer_id}"
            raise PrinterError(msg)

        job = PrintJob(
            printer_id=printer_id,
            type=job_type,
            content=content,
        )

        attempt = 0
        while attempt < self._max_retries:
            attempt += 1
            job.mark_started()

            try:
                self._execute_print(driver, job)
                job.mark_completed()
                logger.info(f"Print job completed: {job.id}")
                return job

            except Exception as e:
                logger.warning(f"Print attempt {attempt} failed: {e}")
                if attempt >= self._max_retries:
                    job.mark_failed(str(e))
                    logger.error(f"Print job failed after {attempt} attempts: {job.id}")
                    raise JobError(f"Print failed after {attempt} attempts: {e}") from e

        return job

    def _execute_print(self, driver: PrinterDriver, job: PrintJob) -> None:
        """Execute print operation based on job type.

        Args:
            driver: Printer driver instance.
            job: Print job entity.
        """
        from src.drivers.escpos_protocol import Alignment, BarcodeFormat, BarcodeOptions, QRCodeOptions, TextOptions

        content = job.content
        data = bytearray()

        # Initialize printer
        data += self._escpos.initialize()

        if job.type == JobType.TEXT:
            options = TextOptions(
                bold=content.get("bold", False),
                double_height=content.get("double_height", False),
                double_width=content.get("double_width", False),
            )
            data += self._escpos.text(content["text"], options=options)

        elif job.type == JobType.BARCODE:
            fmt = BarcodeFormat(content.get("barcode_type", "CODE128"))
            options = BarcodeOptions(
                format=fmt,
                height=content.get("height", 80),
                width=content.get("width", 2),
            )
            data += self._escpos.barcode(content["data"], barcode_format=fmt, options=options)

        elif job.type == JobType.QRCODE:
            options = QRCodeOptions(
                size=content.get("size", 10),
                error_correction=content.get("error_correction", "M"),
            )
            data += self._escpos.qrcode(content["data"], options=options)

        elif job.type == JobType.IMAGE:
            data += self._escpos.image(
                image_path=content.get("image_path"),
                width=content.get("width", 512),
            )

        # Feed and cut
        data += self._escpos.feed(3)
        data += self._escpos.cut()

        # Send all data at once
        driver.send(bytes(data))

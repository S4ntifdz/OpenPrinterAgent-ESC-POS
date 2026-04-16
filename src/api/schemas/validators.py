"""Request schemas for API validation."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CreatePrinterSchema:
    """Schema for creating a new printer."""

    name: str
    connection_type: str
    vendor_id: int | None = None
    product_id: int | None = None
    port: str | None = None
    baudrate: int = 9600

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreatePrinterSchema":
        """Create schema instance from dictionary.

        Args:
            data: Dictionary containing printer data.

        Returns:
            CreatePrinterSchema instance.
        """
        return cls(
            name=data.get("name", ""),
            connection_type=data.get("connection_type", "usb"),
            vendor_id=data.get("vendor_id"),
            product_id=data.get("product_id"),
            port=data.get("port"),
            baudrate=data.get("baudrate", 9600),
        )

    def validate(self) -> list[str]:
        """Validate the schema data.

        Returns:
            List of validation error messages.
        """
        errors = []
        if not self.name:
            errors.append("name is required")
        if self.connection_type not in ("usb", "serial"):
            errors.append("connection_type must be 'usb' or 'serial'")
        if self.connection_type == "usb":
            if self.vendor_id is None or self.product_id is None:
                errors.append("vendor_id and product_id are required for USB printers")
        if self.connection_type == "serial":
            if not self.port:
                errors.append("port is required for serial printers")
        return errors


@dataclass
class PrintTextSchema:
    """Schema for text print job."""

    printer_id: str
    text: str
    bold: bool = False
    double_height: bool = False
    double_width: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrintTextSchema":
        """Create schema instance from dictionary."""
        return cls(
            printer_id=data.get("printer_id", ""),
            text=data.get("text", ""),
            bold=data.get("bold", False),
            double_height=data.get("double_height", False),
            double_width=data.get("double_width", False),
        )

    def validate(self) -> list[str]:
        """Validate the schema data."""
        errors = []
        if not self.printer_id:
            errors.append("printer_id is required")
        if not self.text:
            errors.append("text is required")
        return errors


@dataclass
class PrintBarcodeSchema:
    """Schema for barcode print job."""

    printer_id: str
    data: str
    barcode_type: str = "CODE39"
    height: int = 50
    width: int = 2

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrintBarcodeSchema":
        """Create schema instance from dictionary."""
        return cls(
            printer_id=data.get("printer_id", ""),
            data=data.get("data", ""),
            barcode_type=data.get("barcode_type", "CODE39"),
            height=data.get("height", 50),
            width=data.get("width", 2),
        )

    def validate(self) -> list[str]:
        """Validate the schema data."""
        errors = []
        if not self.printer_id:
            errors.append("printer_id is required")
        if not self.data:
            errors.append("data is required")
        return errors


@dataclass
class PrintQRCodeSchema:
    """Schema for QR code print job."""

    printer_id: str
    data: str
    size: int = 8
    error_correction: str = "L"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrintQRCodeSchema":
        """Create schema instance from dictionary."""
        return cls(
            printer_id=data.get("printer_id", ""),
            data=data.get("data", ""),
            size=data.get("size", 8),
            error_correction=data.get("error_correction", "L"),
        )

    def validate(self) -> list[str]:
        """Validate the schema data."""
        errors = []
        if not self.printer_id:
            errors.append("printer_id is required")
        if not self.data:
            errors.append("data is required")
        if self.error_correction not in ("L", "M", "Q", "H"):
            errors.append("error_correction must be L, M, Q, or H")
        return errors

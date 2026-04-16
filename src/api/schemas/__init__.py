"""Request schemas for OpenPrinterAgent API."""

from src.api.schemas.validators import (
    CreatePrinterSchema,
    PrintBarcodeSchema,
    PrintQRCodeSchema,
    PrintTextSchema,
)

__all__ = [
    "CreatePrinterSchema",
    "PrintTextSchema",
    "PrintBarcodeSchema",
    "PrintQRCodeSchema",
]

"""ESC/POS protocol implementation for OpenPrinterAgent.

This module provides the ESCPOSProtocol class that handles the translation
of high-level print commands (text, images, barcodes, QR codes) into
ESC/POS command byte sequences understood by thermal printers.
"""

from dataclasses import dataclass
from enum import Enum


class BarcodeFormat(Enum):
    """Supported barcode formats for ESC/POS printers."""

    CODE128 = "CODE128"
    CODE39 = "CODE39"
    EAN13 = "EAN13"
    EAN8 = "EAN8"
    UPCA = "UPC-A"
    UPCE = "UPC-E"
    I25 = "I25"


class Alignment(Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Font(Enum):
    """Font options for text printing."""

    A = "a"
    B = "b"


@dataclass
class TextOptions:
    """Options for text printing.

    Attributes:
        alignment: Text alignment (left, center, right).
        font: Font selection (a or b).
        bold: Enable bold text.
        underline: Enable underline.
        double_height: Double height text.
        double_width: Double width text.
    """

    alignment: Alignment = Alignment.LEFT
    font: Font = Font.A
    bold: bool = False
    underline: bool = False
    double_height: bool = False
    double_width: bool = False


@dataclass
class QRCodeOptions:
    """Options for QR code printing.

    Attributes:
        size: QR code size (1-16).
        error_correction: Error correction level (L, M, Q, H).
    """

    size: int = 10
    error_correction: str = "M"


@dataclass
class BarcodeOptions:
    """Options for barcode printing.

    Attributes:
        format: Barcode format.
        height: Barcode height in dots.
        width: Barcode width (1-3).
        align: Text alignment below barcode.
    """

    format: BarcodeFormat = BarcodeFormat.CODE128
    height: int = 80
    width: int = 2
    align: Alignment = Alignment.CENTER


class ESCPOSProtocol:
    """ESC/POS protocol handler.

    This class provides methods to generate ESC/POS command sequences
    for various print operations. It handles the low-level details
    of the ESC/POS command language used by most thermal printers.

    Attributes:
        encoding: Character encoding for text (default: 'utf-8').
    """

    ESC = b"\x1b"
    GS = b"\x1d"
    LF = b"\n"

    INIT_SEQUENCE = ESC + b"@"  # Initialize printer
    CUT_SEQUENCE = GS + b"V\x00"  # Full cut
    PARTIAL_CUT = GS + b"V\x01"  # Partial cut
    FEED_AND_CUT = ESC + b"d\x03" + GS + b"V\x00"  # Feed 3 lines and cut

    def __init__(self, encoding: str = "utf-8") -> None:
        """Initialize ESC/POS protocol handler.

        Args:
            encoding: Character encoding for text output.
        """
        self._encoding = encoding

    def text(self, content: str, options: TextOptions | None = None) -> bytes:
        """Generate ESC/POS commands for text.

        Args:
            content: Text string to print.
            options: Text formatting options.

        Returns:
            ESC/POS byte sequence for the text.
        """
        if options is None:
            options = TextOptions()

        commands = bytearray()

        commands += self._text_format(options)
        commands += content.encode(self._encoding)
        commands += self.LF

        return bytes(commands)

    def _text_format(self, options: TextOptions) -> bytes:
        """Generate text formatting commands.

        Args:
            options: Text formatting options.

        Returns:
            ESC/POS formatting commands.
        """
        commands = bytearray()

        alignment_map = {
            Alignment.LEFT: 0,
            Alignment.CENTER: 1,
            Alignment.RIGHT: 2,
        }
        commands += self.ESC + b"a%d" % alignment_map[options.alignment]

        font_map = {Font.A: 0, Font.B: 1}
        commands += self.ESC + b"M%d" % font_map[options.font]

        commands += self.ESC + b"E%d" % (1 if options.bold else 0)
        commands += self.ESC + b"-%d" % (1 if options.underline else 0)

        commands += self.ESC + b"!\x10" if options.double_height else self.ESC + b"!\x00"
        if options.double_width:
            current = commands[-1] if commands else 0
            commands[-1] = current | 0x10

        return bytes(commands)

    def barcode(
        self, data: str, barcode_format: BarcodeFormat, options: BarcodeOptions | None = None
    ) -> bytes:
        """Generate ESC/POS commands for barcode.

        Args:
            data: Data to encode in barcode.
            barcode_format: Format of the barcode.
            options: Barcode formatting options.

        Returns:
            ESC/POS byte sequence for the barcode.
        """
        if options is None:
            options = BarcodeOptions(format=barcode_format)

        commands = bytearray()

        barcode_types: dict[BarcodeFormat, int] = {
            BarcodeFormat.CODE128: 73,
            BarcodeFormat.CODE39: 69,
            BarcodeFormat.EAN13: 67,
            BarcodeFormat.EAN8: 68,
            BarcodeFormat.UPCA: 65,
            BarcodeFormat.UPCE: 66,
            BarcodeFormat.I25: 73,
        }

        barcode_type = barcode_types.get(options.format, 73)

        commands += self.GS + b"w%d" % options.width
        commands += self.GS + b"h%d" % options.height
        commands += self.GS + b"H%d" % 2

        commands += self.GS + b"k%d" % barcode_type
        commands += data.encode("ascii")
        commands += b"\x00"

        commands += self.LF

        return bytes(commands)

    def qrcode(self, data: str, options: QRCodeOptions | None = None) -> bytes:
        """Generate ESC/POS commands for QR code.

        Args:
            data: Data to encode in QR code.
            options: QR code formatting options.

        Returns:
            ESC/POS byte sequence for the QR code.
        """
        if options is None:
            options = QRCodeOptions()

        commands = bytearray()

        error_levels: dict[str, int] = {"L": 0, "M": 1, "Q": 2, "H": 3}
        error_level = error_levels.get(options.error_correction, 1)

        model_command = self.GS + b"(k\x04\x00\x31\x41\x32\x00"
        commands += model_command

        size_command = self.GS + b"(k\x03\x00\x31\x43\x00" + bytes([options.size])
        commands += size_command

        error_command = self.GS + b"(k\x03\x00\x31\x45\x00" + bytes([error_level + 48])
        commands += error_command

        data_bytes = data.encode("utf-8")
        data_len = len(data_bytes) + 3
        high_byte = (data_len >> 8) & 0xFF
        low_byte = data_len & 0xFF

        store_command = self.GS + b"(k" + bytes([low_byte, high_byte]) + b"\x31\x50\x30"
        commands += store_command
        commands += data_bytes

        print_command = self.GS + b"(k\x03\x00\x31\x51\x00"
        commands += print_command

        commands += self.LF

        return bytes(commands)

    def image(
        self,
        image_path: str | None = None,
        image_data: bytes | None = None,
        width: int = 200,
    ) -> bytes:
        """Generate ESC/POS commands for image using raster bit image mode.

        Args:
            image_path: Path to image file.
            image_data: Raw image bytes (alternative to path).
            width: Width to scale image to in pixels.

        Returns:
            ESC/POS byte sequence for the image.
        """
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            return b""

        commands = bytearray()

        if image_path:
            img = Image.open(image_path)
        elif image_data:
            img = Image.open(BytesIO(image_data))
        else:
            return bytes(commands)

        img = img.convert("1")

        original_width = img.width
        ratio = width / original_width if original_width > 0 else 1
        new_height = int(img.height * ratio)
        if new_height > 0:
            img = img.resize((width, new_height), Image.Resampling.LANCZOS)

        width_bytes = (width + 7) // 8

        nl_value = width_bytes & 0xFF
        nh_value = (width_bytes >> 8) & 0xFF

        commands += (
            self.GS
            + b"v\x00"
            + bytes([nl_value, nh_value, new_height & 0xFF, (new_height >> 8) & 0xFF])
        )

        img_bytes = img.tobytes()
        for y in range(new_height):
            row_start = y * width_bytes
            row_end = row_start + width_bytes
            row_data = img_bytes[row_start:row_end]
            commands += b"\x1b*?" + bytes([nl_value, nh_value]) + row_data

        commands += self.LF

        return bytes(commands)

    def initialize(self) -> bytes:
        """Get printer initialization sequence.

        Returns:
            ESC/POS initialization commands.
        """
        return self.INIT_SEQUENCE

    def cut(self, partial: bool = False) -> bytes:
        """Get paper cut command.

        Args:
            partial: Use partial cut instead of full cut.

        Returns:
            ESC/POS cut command.
        """
        if partial:
            return self.PARTIAL_CUT
        return self.CUT_SEQUENCE

    def feed(self, lines: int = 3) -> bytes:
        """Get paper feed command.

        Args:
            lines: Number of lines to feed.

        Returns:
            ESC/POS feed command.
        """
        return self.ESC + b"d" + bytes([lines])

    def beep(self) -> bytes:
        """Get buzzer/beep command.

        Returns:
            ESC/POS beep command.
        """
        return self.ESC + b"p\x00\x01\xff"

    def status_request(self) -> bytes:
        """Get printer status request command.

        Returns:
            ESC/POS status request command.
        """
        return self.ESC + b"v\x00"

    def bold(self, enable: bool = True) -> bytes:
        """Get bold text command.

        Args:
            enable: Enable or disable bold.

        Returns:
            ESC/POS bold command.
        """
        return self.ESC + b"E" + bytes([1 if enable else 0])

    def underline(self, enable: bool = True) -> bytes:
        """Get underline text command.

        Args:
            enable: Enable or disable underline.

        Returns:
            ESC/POS underline command.
        """
        return self.ESC + b"-" + bytes([1 if enable else 0])

    def line_spacing(self, dots: int = 30) -> bytes:
        """Get line spacing command.

        Args:
            dots: Line spacing in dots.

        Returns:
            ESC/POS line spacing command.
        """
        return self.ESC + b"3" + bytes([dots])

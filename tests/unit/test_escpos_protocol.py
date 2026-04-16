"""Unit tests for ESCPOSProtocol class."""


from src.drivers.escpos_protocol import (
    Alignment,
    BarcodeFormat,
    BarcodeOptions,
    ESCPOSProtocol,
    Font,
    QRCodeOptions,
    TextOptions,
)


class TestESCPOSProtocolInit:
    """Tests for ESCPOSProtocol initialization."""

    def test_default_encoding(self) -> None:
        """Test default encoding is utf-8."""
        protocol = ESCPOSProtocol()
        assert protocol._encoding == "utf-8"

    def test_custom_encoding(self) -> None:
        """Test custom encoding."""
        protocol = ESCPOSProtocol(encoding="latin-1")
        assert protocol._encoding == "latin-1"


class TestTextCommands:
    """Tests for text command generation."""

    def test_simple_text(self) -> None:
        """Test simple text command."""
        protocol = ESCPOSProtocol()
        result = protocol.text("Hello")
        assert b"Hello" in result
        assert result.endswith(b"\n")

    def test_text_with_options(self) -> None:
        """Test text with formatting options."""
        protocol = ESCPOSProtocol()
        options = TextOptions(
            alignment=Alignment.CENTER,
            font=Font.B,
            bold=True,
            underline=True,
        )
        result = protocol.text("Hello", options)
        assert b"Hello" in result

    def test_text_default_options(self) -> None:
        """Test text with default options."""
        protocol = ESCPOSProtocol()
        result = protocol.text("Test")
        assert b"Test" in result


class TestAlignment:
    """Tests for Alignment enum."""

    def test_alignment_values(self) -> None:
        """Test alignment enum values."""
        assert Alignment.LEFT.value == "left"
        assert Alignment.CENTER.value == "center"
        assert Alignment.RIGHT.value == "right"


class TestFont:
    """Tests for Font enum."""

    def test_font_values(self) -> None:
        """Test font enum values."""
        assert Font.A.value == "a"
        assert Font.B.value == "b"


class TestBarcodeFormat:
    """Tests for BarcodeFormat enum."""

    def test_barcode_formats(self) -> None:
        """Test barcode format values."""
        assert BarcodeFormat.CODE128.value == "CODE128"
        assert BarcodeFormat.CODE39.value == "CODE39"
        assert BarcodeFormat.EAN13.value == "EAN13"
        assert BarcodeFormat.EAN8.value == "EAN8"
        assert BarcodeFormat.UPCA.value == "UPC-A"
        assert BarcodeFormat.UPCE.value == "UPC-E"
        assert BarcodeFormat.I25.value == "I25"


class TestTextOptions:
    """Tests for TextOptions dataclass."""

    def test_default_options(self) -> None:
        """Test default text options."""
        options = TextOptions()
        assert options.alignment == Alignment.LEFT
        assert options.font == Font.A
        assert options.bold is False
        assert options.underline is False
        assert options.double_height is False
        assert options.double_width is False

    def test_custom_options(self) -> None:
        """Test custom text options."""
        options = TextOptions(
            alignment=Alignment.CENTER,
            font=Font.B,
            bold=True,
            double_height=True,
        )
        assert options.alignment == Alignment.CENTER
        assert options.font == Font.B
        assert options.bold is True
        assert options.double_height is True


class TestBarcodeOptions:
    """Tests for BarcodeOptions dataclass."""

    def test_default_options(self) -> None:
        """Test default barcode options."""
        options = BarcodeOptions()
        assert options.format == BarcodeFormat.CODE128
        assert options.height == 80
        assert options.width == 2
        assert options.align == Alignment.CENTER

    def test_custom_options(self) -> None:
        """Test custom barcode options."""
        options = BarcodeOptions(
            format=BarcodeFormat.EAN13,
            height=100,
            width=3,
        )
        assert options.format == BarcodeFormat.EAN13
        assert options.height == 100
        assert options.width == 3


class TestQRCodeOptions:
    """Tests for QRCodeOptions dataclass."""

    def test_default_options(self) -> None:
        """Test default QR code options."""
        options = QRCodeOptions()
        assert options.size == 10
        assert options.error_correction == "M"

    def test_custom_options(self) -> None:
        """Test custom QR code options."""
        options = QRCodeOptions(size=12, error_correction="H")
        assert options.size == 12
        assert options.error_correction == "H"


class TestBarcodeCommand:
    """Tests for barcode command generation."""

    def test_barcode_basic(self) -> None:
        """Test basic barcode generation."""
        protocol = ESCPOSProtocol()
        result = protocol.barcode("123456789", BarcodeFormat.CODE128)
        assert b"123456789" in result
        assert len(result) > 10

    def test_barcode_with_options(self) -> None:
        """Test barcode with custom options."""
        protocol = ESCPOSProtocol()
        options = BarcodeOptions(
            format=BarcodeFormat.CODE39,
            height=100,
            width=3,
        )
        result = protocol.barcode("ABC123", BarcodeFormat.CODE39, options)
        assert b"ABC123" in result


class TestQRCodeCommand:
    """Tests for QR code command generation."""

    def test_qrcode_basic(self) -> None:
        """Test basic QR code generation."""
        protocol = ESCPOSProtocol()
        result = protocol.qrcode("https://example.com")
        assert len(result) > 20

    def test_qrcode_with_options(self) -> None:
        """Test QR code with custom options."""
        protocol = ESCPOSProtocol()
        options = QRCodeOptions(size=8, error_correction="L")
        result = protocol.qrcode("test data", options)
        assert len(result) > 20


class TestPrinterCommands:
    """Tests for printer control commands."""

    def test_initialize(self) -> None:
        """Test initialize command."""
        protocol = ESCPOSProtocol()
        result = protocol.initialize()
        assert len(result) > 0

    def test_cut_full(self) -> None:
        """Test full cut command."""
        protocol = ESCPOSProtocol()
        result = protocol.cut(partial=False)
        assert len(result) > 0

    def test_cut_partial(self) -> None:
        """Test partial cut command."""
        protocol = ESCPOSProtocol()
        result = protocol.cut(partial=True)
        assert len(result) > 0

    def test_feed(self) -> None:
        """Test feed command."""
        protocol = ESCPOSProtocol()
        result = protocol.feed(lines=5)
        assert b"\x1bd\x05" in result

    def test_beep(self) -> None:
        """Test beep command."""
        protocol = ESCPOSProtocol()
        result = protocol.beep()
        assert len(result) > 0

    def test_status_request(self) -> None:
        """Test status request command."""
        protocol = ESCPOSProtocol()
        result = protocol.status_request()
        assert len(result) > 0

    def test_bold_on(self) -> None:
        """Test bold on command."""
        protocol = ESCPOSProtocol()
        result = protocol.bold(enable=True)
        assert result == b"\x1bE\x01"

    def test_bold_off(self) -> None:
        """Test bold off command."""
        protocol = ESCPOSProtocol()
        result = protocol.bold(enable=False)
        assert result == b"\x1bE\x00"

    def test_underline_on(self) -> None:
        """Test underline on command."""
        protocol = ESCPOSProtocol()
        result = protocol.underline(enable=True)
        assert result == b"\x1b-\x01"

    def test_underline_off(self) -> None:
        """Test underline off command."""
        protocol = ESCPOSProtocol()
        result = protocol.underline(enable=False)
        assert result == b"\x1b-\x00"

    def test_line_spacing(self) -> None:
        """Test line spacing command."""
        protocol = ESCPOSProtocol()
        result = protocol.line_spacing(dots=24)
        assert b"\x1b3\x18" in result


class TestImageCommand:
    """Tests for image command generation."""

    def test_image_no_source(self) -> None:
        """Test image with no source returns empty."""
        protocol = ESCPOSProtocol()
        result = protocol.image()
        assert result == b""

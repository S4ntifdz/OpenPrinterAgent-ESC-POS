"""Integration tests for the OpenPrinterAgent API."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.api.app import create_app
from src.core.entities import ConnectionType, PrinterStatus
from src.models.database import Database


@pytest.fixture
def app(tmp_path: Path) -> Any:
    """Create test Flask application.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Configured Flask test client.
    """
    from src.utils.config import Config

    config = Config(
        FLASK_ENV="testing",
        FLASK_DEBUG=False,
        API_HOST="127.0.0.1",
        API_PORT=5000,
        API_SECRET_KEY="test-secret",
        API_KEY="test-api-key",
        DATABASE_PATH=tmp_path / "test.db",
        DEFAULT_BAUDRATE=9600,
        DEFAULT_CONNECTION="usb",
        LOG_LEVEL="DEBUG",
        LOG_FILE=tmp_path / "test.log",
        CORS_ORIGINS="http://localhost:3000",
    )

    app = create_app(config)
    app.config["TESTING"] = True

    db = Database(config.DATABASE_PATH)
    db.init_schema()

    return app


@pytest.fixture
def client(app: Any) -> Any:
    """Create Flask test client.

    Args:
        app: Flask application fixture.

    Returns:
        Flask test client.
    """
    return app.test_client()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Get authentication headers for API requests.

    Returns:
        Dictionary with X-API-Key header.
    """
    return {"X-API-Key": "test-api-key"}


class TestStatusEndpoint:
    """Tests for status endpoint (public, no auth required)."""

    def test_get_status(self, client: Any) -> None:
        """Test getting system status."""
        response = client.get("/api/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"
        assert "printers_connected" in data
        assert "printers_total" in data
        assert "jobs_pending" in data
        assert "uptime_seconds" in data


class TestPrinterEndpoints:
    """Tests for printer management endpoints."""

    def test_list_printers_unauthorized(self, client: Any) -> None:
        """Test listing printers without auth returns 401."""
        response = client.get("/api/printers")
        assert response.status_code == 401

    def test_list_printers_authorized(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test listing printers with valid auth."""
        response = client.get("/api/printers", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "printers" in data
        assert isinstance(data["printers"], list)

    def test_create_printer_usb(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test creating a USB printer."""
        payload = {
            "name": "Test USB Printer",
            "connection_type": "usb",
            "vendor_id": 0x04B8,
            "product_id": 0x0202,
        }

        response = client.post(
            "/api/printers",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["printer"]["name"] == "Test USB Printer"
        assert data["printer"]["connection_type"] == "usb"

    def test_create_printer_serial(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test creating a Serial printer."""
        payload = {
            "name": "Test Serial Printer",
            "connection_type": "serial",
            "port": "/dev/ttyUSB0",
            "baudrate": 115200,
        }

        response = client.post(
            "/api/printers",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["printer"]["name"] == "Test Serial Printer"
        assert data["printer"]["connection_type"] == "serial"

    def test_create_printer_validation_error(
        self, client: Any, auth_headers: dict[str, str]
    ) -> None:
        """Test creating printer with invalid data."""
        payload = {
            "name": "",
            "connection_type": "usb",
        }

        response = client.post(
            "/api/printers",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_create_printer_missing_usb_fields(
        self, client: Any, auth_headers: dict[str, str]
    ) -> None:
        """Test creating USB printer without vendor/product ID."""
        payload = {
            "name": "Test Printer",
            "connection_type": "usb",
        }

        response = client.post(
            "/api/printers",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_get_printer(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test getting a printer by ID."""
        create_payload = {
            "name": "Test Printer",
            "connection_type": "usb",
            "vendor_id": 0x04B8,
            "product_id": 0x0202,
        }

        create_response = client.post(
            "/api/printers",
            data=json.dumps(create_payload),
            content_type="application/json",
            headers=auth_headers,
        )
        printer_id = json.loads(create_response.data)["printer"]["id"]

        response = client.get(f"/api/printers/{printer_id}", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["printer"]["id"] == printer_id

    def test_get_printer_not_found(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test getting a non-existent printer."""
        response = client.get("/api/printers/non-existent-id", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_printer(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test deleting a printer."""
        create_payload = {
            "name": "Test Printer",
            "connection_type": "usb",
            "vendor_id": 0x04B8,
            "product_id": 0x0202,
        }

        create_response = client.post(
            "/api/printers",
            data=json.dumps(create_payload),
            content_type="application/json",
            headers=auth_headers,
        )
        printer_id = json.loads(create_response.data)["printer"]["id"]

        response = client.delete(f"/api/printers/{printer_id}", headers=auth_headers)

        assert response.status_code == 200

        get_response = client.get(f"/api/printers/{printer_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_connect_printer_not_found(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test connecting a non-existent printer."""
        response = client.post("/api/printers/non-existent-id/connect", headers=auth_headers)

        assert response.status_code == 400


class TestJobEndpoints:
    """Tests for print job endpoints."""

    def test_list_jobs_unauthorized(self, client: Any) -> None:
        """Test listing jobs without auth returns 401."""
        response = client.get("/api/jobs")
        assert response.status_code == 401

    def test_list_jobs_authorized(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test listing jobs with valid auth."""
        response = client.get("/api/jobs", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_get_job_not_found(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test getting a non-existent job."""
        response = client.get("/api/jobs/non-existent-id", headers=auth_headers)

        assert response.status_code == 404

    def test_cancel_job_not_found(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test cancelling a non-existent job."""
        response = client.delete("/api/jobs/non-existent-id", headers=auth_headers)

        assert response.status_code == 404


class TestPrintEndpoint:
    """Tests for print endpoint."""

    def test_print_unauthorized(self, client: Any) -> None:
        """Test printing without auth returns 401."""
        payload = {
            "type": "text",
            "printer_id": "test-id",
            "text": "Hello",
        }

        response = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_print_text_printer_not_found(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test printing to non-existent printer."""
        payload = {
            "type": "text",
            "printer_id": "non-existent-id",
            "text": "Hello",
        }

        response = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_print_validation_error(self, client: Any, auth_headers: dict[str, str]) -> None:
        """Test printing with invalid payload."""
        payload = {
            "type": "text",
        }

        response = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400


class TestCORs:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client: Any) -> None:
        """Test CORS headers are present in response."""
        response = client.get("/api/status")

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

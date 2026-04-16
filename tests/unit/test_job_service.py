"""Unit tests for job service."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.core.entities import JobStatus, JobType, PrintJob
from src.core.exceptions import JobError
from src.models.database import Database
from src.services.job_service import JobService


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Create test database."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.init_schema()
    return db


@pytest.fixture
def job_service(db: Database) -> JobService:
    """Create JobService instance."""
    return JobService(db)


@pytest.fixture
def sample_printer(db: Database) -> dict[str, Any]:
    """Create sample printer in database."""
    from src.core.entities import ConnectionType
    from src.services.printer_service import PrinterService

    ps = PrinterService(db)
    printer = ps.add_printer(
        name="Test Printer",
        connection_type=ConnectionType.USB,
        vendor_id=0x04B8,
        product_id=0x0202,
    )
    return {"id": printer.id, "ps": ps}


class TestJobService:
    """Tests for JobService class."""

    def test_create_job(self, job_service: JobService, sample_printer: dict) -> None:
        """Test creating a print job."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Hello, World!"},
        )

        assert job.printer_id == sample_printer["id"]
        assert job.type == JobType.TEXT
        assert job.content["text"] == "Hello, World!"
        assert job.status == JobStatus.PENDING

    def test_create_job_barcode(self, job_service: JobService, sample_printer: dict) -> None:
        """Test creating a barcode print job."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.BARCODE,
            content={"data": "123456789", "barcode_type": "CODE128"},
        )

        assert job.type == JobType.BARCODE
        assert job.content["barcode_type"] == "CODE128"

    def test_create_job_qrcode(self, job_service: JobService, sample_printer: dict) -> None:
        """Test creating a QR code print job."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.QRCODE,
            content={"data": "https://example.com", "size": 10},
        )

        assert job.type == JobType.QRCODE
        assert job.content["size"] == 10

    def test_get_job(self, job_service: JobService, sample_printer: dict) -> None:
        """Test getting a job by ID."""
        created = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Test"},
        )

        retrieved = job_service.get_job(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_job_not_found(self, job_service: JobService) -> None:
        """Test getting non-existent job."""
        result = job_service.get_job("non-existent-id")
        assert result is None

    def test_list_jobs(self, job_service: JobService, sample_printer: dict) -> None:
        """Test listing all jobs."""
        job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 1"},
        )
        job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 2"},
        )

        jobs = job_service.list_jobs()

        assert len(jobs) == 2

    def test_list_jobs_by_printer(self, job_service: JobService, db: Database) -> None:
        """Test listing jobs filtered by printer."""
        from src.core.entities import ConnectionType
        from src.services.printer_service import PrinterService

        ps = PrinterService(db)
        p1 = ps.add_printer(
            name="P1", connection_type=ConnectionType.USB, vendor_id=1, product_id=1
        )
        p2 = ps.add_printer(
            name="P2", connection_type=ConnectionType.USB, vendor_id=2, product_id=2
        )

        job_service.create_job(printer_id=p1.id, job_type=JobType.TEXT, content={"text": "A"})
        job_service.create_job(printer_id=p1.id, job_type=JobType.TEXT, content={"text": "B"})
        job_service.create_job(printer_id=p2.id, job_type=JobType.TEXT, content={"text": "C"})

        jobs_p1 = job_service.list_jobs(printer_id=p1.id)
        jobs_p2 = job_service.list_jobs(printer_id=p2.id)

        assert len(jobs_p1) == 2
        assert len(jobs_p2) == 1

    def test_list_jobs_by_status(self, job_service: JobService, sample_printer: dict) -> None:
        """Test listing jobs filtered by status."""
        job1 = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Pending"},
        )
        job2 = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Completed"},
        )
        job_service.update_job_status(job1.id, JobStatus.COMPLETED)

        pending = job_service.list_jobs(status=JobStatus.PENDING)
        completed = job_service.list_jobs(status=JobStatus.COMPLETED)

        assert len(pending) == 1
        assert len(completed) == 1

    def test_list_jobs_with_limit(self, job_service: JobService, sample_printer: dict) -> None:
        """Test listing jobs with limit."""
        for i in range(5):
            job_service.create_job(
                printer_id=sample_printer["id"],
                job_type=JobType.TEXT,
                content={"text": f"Job {i}"},
            )

        jobs = job_service.list_jobs(limit=3)

        assert len(jobs) == 3


class TestJobServiceCancellation:
    """Tests for JobService cancellation."""

    def test_cancel_pending_job(self, job_service: JobService, sample_printer: dict) -> None:
        """Test cancelling a pending job."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Test"},
        )

        cancelled = job_service.cancel_job(job.id)

        assert cancelled is not None
        assert cancelled.status == JobStatus.CANCELLED

    def test_cancel_non_pending_job_fails(
        self, job_service: JobService, sample_printer: dict
    ) -> None:
        """Test cancelling non-pending job raises error."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Test"},
        )
        job_service.update_job_status(job.id, JobStatus.COMPLETED)

        with pytest.raises(JobError, match="Cannot cancel job"):
            job_service.cancel_job(job.id)

    def test_cancel_non_existent_job(self, job_service: JobService) -> None:
        """Test cancelling non-existent job returns None."""
        result = job_service.cancel_job("non-existent-id")
        assert result is None


class TestJobServiceStatusUpdate:
    """Tests for JobService status updates."""

    def test_update_job_status(self, job_service: JobService, sample_printer: dict) -> None:
        """Test updating job status."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Test"},
        )

        updated = job_service.update_job_status(job.id, JobStatus.PRINTING)

        assert updated is not None
        assert updated.status == JobStatus.PRINTING
        assert updated.started_at is not None

    def test_update_job_status_with_error(
        self, job_service: JobService, sample_printer: dict
    ) -> None:
        """Test updating job status with error message."""
        job = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Test"},
        )

        updated = job_service.update_job_status(job.id, JobStatus.FAILED, error="Paper jam")

        assert updated is not None
        assert updated.status == JobStatus.FAILED
        assert updated.error == "Paper jam"
        assert updated.completed_at is not None

    def test_update_job_status_not_found(self, job_service: JobService) -> None:
        """Test updating non-existent job returns None."""
        result = job_service.update_job_status("non-existent-id", JobStatus.PRINTING)
        assert result is None


class TestJobServiceQueries:
    """Tests for JobService query methods."""

    def test_get_pending_jobs(self, job_service: JobService, sample_printer: dict) -> None:
        """Test getting pending jobs for a printer."""
        job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 1"},
        )
        job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 2"},
        )
        job3 = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 3"},
        )
        job_service.update_job_status(job3.id, JobStatus.COMPLETED)

        pending = job_service.get_pending_jobs(sample_printer["id"])

        assert len(pending) == 2
        assert all(j.status == JobStatus.PENDING for j in pending)

    def test_get_job_history(self, job_service: JobService, sample_printer: dict) -> None:
        """Test getting job history (completed/failed jobs)."""
        job1 = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 1"},
        )
        job2 = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 2"},
        )
        job3 = job_service.create_job(
            printer_id=sample_printer["id"],
            job_type=JobType.TEXT,
            content={"text": "Job 3"},
        )

        job_service.update_job_status(job1.id, JobStatus.COMPLETED)
        job_service.update_job_status(job2.id, JobStatus.FAILED)
        job_service.update_job_status(job3.id, JobStatus.PRINTING)

        history = job_service.get_job_history(sample_printer["id"])

        assert len(history) == 2
        assert all(j.status in (JobStatus.COMPLETED, JobStatus.FAILED) for j in history)

    def test_get_job_history_by_printer(self, job_service: JobService, db: Database) -> None:
        """Test getting job history filtered by printer."""
        from src.core.entities import ConnectionType
        from src.services.printer_service import PrinterService

        ps = PrinterService(db)
        p1 = ps.add_printer(
            name="P1", connection_type=ConnectionType.USB, vendor_id=1, product_id=1
        )
        p2 = ps.add_printer(
            name="P2", connection_type=ConnectionType.USB, vendor_id=2, product_id=2
        )

        j1 = job_service.create_job(printer_id=p1.id, job_type=JobType.TEXT, content={"text": "A"})
        j2 = job_service.create_job(printer_id=p2.id, job_type=JobType.TEXT, content={"text": "B"})

        job_service.update_job_status(j1.id, JobStatus.COMPLETED)
        job_service.update_job_status(j2.id, JobStatus.COMPLETED)

        history_p1 = job_service.get_job_history(printer_id=p1.id)

        assert len(history_p1) == 1
        assert history_p1[0].printer_id == p1.id

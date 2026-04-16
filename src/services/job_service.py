"""Job management service for OpenPrinterAgent.

This module provides the JobService class that handles the business
logic for managing print jobs: creation, status tracking, listing, and cancellation.
"""

import json
from typing import Any

from src.core.entities import JobStatus, JobType, PrintJob
from src.core.exceptions import JobError
from src.models.database import Database
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobService:
    """Service for managing print jobs.

    This service provides business logic for print job management operations
    including CRUD operations, status tracking, and job cancellation.

    Attributes:
        database: Database instance for persistence.
    """

    def __init__(self, database: Database) -> None:
        """Initialize job service.

        Args:
            database: Database instance for persistence.
        """
        self._db = database

    def create_job(
        self,
        printer_id: str,
        job_type: JobType,
        content: dict[str, Any],
    ) -> PrintJob:
        """Create a new print job.

        Args:
            printer_id: ID of the printer to use.
            job_type: Type of print job.
            content: Job content data.

        Returns:
            The created PrintJob entity.

        Raises:
            JobError: If validation fails.
        """
        job = PrintJob(
            printer_id=printer_id,
            type=job_type,
            content=content,
        )

        query = """
        INSERT INTO print_jobs (id, printer_id, type, content, status, error, created_at, started_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self._db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    job.id,
                    job.printer_id,
                    job.type.value,
                    json.dumps(job.content),
                    job.status.value,
                    job.error,
                    job.created_at.isoformat(),
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                ),
            )

        logger.info(f"Print job created: {job.id}")
        return job

    def get_job(self, job_id: str) -> PrintJob | None:
        """Get a print job by ID.

        Args:
            job_id: ID of the print job.

        Returns:
            PrintJob entity or None if not found.
        """
        query = "SELECT * FROM print_jobs WHERE id = ?"

        with self._db.get_cursor() as cursor:
            cursor.execute(query, (job_id,))
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def list_jobs(
        self,
        printer_id: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[PrintJob]:
        """List print jobs with optional filters.

        Args:
            printer_id: Filter by printer ID.
            status: Filter by job status.
            limit: Maximum number of jobs to return.

        Returns:
            List of PrintJob entities.
        """
        conditions = []
        params: list[Any] = []

        if printer_id is not None:
            conditions.append("printer_id = ?")
            params.append(printer_id)

        if status is not None:
            conditions.append("status = ?")
            params.append(status.value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM print_jobs WHERE {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._db.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    def cancel_job(self, job_id: str) -> PrintJob | None:
        """Cancel a print job.

        Only pending jobs can be cancelled.

        Args:
            job_id: ID of the print job to cancel.

        Returns:
            Updated PrintJob entity or None if not found.

        Raises:
            JobError: If job is not in pending status.
        """
        job = self.get_job(job_id)
        if job is None:
            return None

        if job.status != JobStatus.PENDING:
            msg = f"Cannot cancel job in status: {job.status.value}"
            raise JobError(msg)

        job.mark_cancelled()
        self._update_job(job)

        logger.info(f"Print job cancelled: {job.id}")
        return job

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: str | None = None,
    ) -> PrintJob | None:
        """Update print job status.

        Args:
            job_id: ID of the print job.
            status: New status.
            error: Error message if status is FAILED.

        Returns:
            Updated PrintJob entity or None if not found.
        """
        job = self.get_job(job_id)
        if job is None:
            return None

        job.status = status
        if error is not None:
            job.error = error

        if status == JobStatus.PRINTING and job.started_at is None:
            from datetime import datetime, timezone

            job.started_at = datetime.now(timezone.utc)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            from datetime import datetime, timezone

            job.completed_at = datetime.now(timezone.utc)

        self._update_job(job)
        return job

    def get_pending_jobs(self, printer_id: str) -> list[PrintJob]:
        """Get pending jobs for a printer.

        Args:
            printer_id: ID of the printer.

        Returns:
            List of pending PrintJob entities.
        """
        return self.list_jobs(printer_id=printer_id, status=JobStatus.PENDING)

    def get_job_history(
        self,
        printer_id: str | None = None,
        limit: int = 50,
    ) -> list[PrintJob]:
        """Get completed and failed jobs (history).

        Args:
            printer_id: Filter by printer ID.
            limit: Maximum number of jobs to return.

        Returns:
            List of historical PrintJob entities.
        """
        conditions = ["status IN (?, ?)"]
        params: list[Any] = [JobStatus.COMPLETED.value, JobStatus.FAILED.value]

        if printer_id is not None:
            conditions.append("printer_id = ?")
            params.append(printer_id)

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM print_jobs WHERE {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._db.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    def _update_job(self, job: PrintJob) -> None:
        """Update a print job in the database.

        Args:
            job: PrintJob entity to update.
        """
        query = """
        UPDATE print_jobs
        SET status = ?, error = ?, started_at = ?, completed_at = ?
        WHERE id = ?
        """

        with self._db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    job.status.value,
                    job.error,
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.id,
                ),
            )

    def _row_to_job(self, row: Any) -> PrintJob:
        """Convert database row to PrintJob entity.

        Args:
            row: Database row.

        Returns:
            PrintJob entity.
        """
        from datetime import datetime

        started_at = None
        completed_at = None

        if row["started_at"]:
            started_at = datetime.fromisoformat(row["started_at"])
        if row["completed_at"]:
            completed_at = datetime.fromisoformat(row["completed_at"])

        return PrintJob(
            id=row["id"],
            printer_id=row["printer_id"],
            type=JobType(row["type"]),
            content=json.loads(row["content"]),
            status=JobStatus(row["status"]),
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=started_at,
            completed_at=completed_at,
        )

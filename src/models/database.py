"""Database connection and session management for OpenPrinterAgent.

This module provides the Database class that handles SQLite connections
and provides session management for repository operations.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database connection manager.

    This class manages database connections and provides utility methods
    for initializing the database schema.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize database connection manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = Path(db_path)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        """Get database path.

        Returns:
            Path to the database file.
        """
        return self._db_path

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Get a database connection as a context manager.

        Yields:
            SQLite connection object.

        Example:
            with db.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM printers")
        """
        import sqlite3

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Get a database cursor as a context manager.

        Yields:
            SQLite cursor object.

        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM printers")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def init_schema(self) -> None:
        """Initialize database schema with required tables.

        Creates the printers and print_jobs tables if they don't exist.
        """
        schema = """
        CREATE TABLE IF NOT EXISTS printers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            connection_type TEXT NOT NULL,
            vendor_id INTEGER,
            product_id INTEGER,
            port TEXT,
            baudrate INTEGER DEFAULT 9600,
            status TEXT DEFAULT 'disconnected',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS print_jobs (
            id TEXT PRIMARY KEY,
            printer_id TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            error TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (printer_id) REFERENCES printers (id)
        );

        CREATE INDEX IF NOT EXISTS idx_print_jobs_printer_id
            ON print_jobs (printer_id);
        CREATE INDEX IF NOT EXISTS idx_print_jobs_status
            ON print_jobs (status);
        CREATE INDEX IF NOT EXISTS idx_printers_status
            ON printers (status);
        """

        with self.get_cursor() as cursor:
            cursor.executescript(schema)

        logger.info("Database schema initialized successfully")

    def close(self) -> None:
        """Close any open connections (no-op for SQLite)."""

    def __enter__(self) -> "Database":
        """Enter context manager.

        Returns:
            Database instance.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()

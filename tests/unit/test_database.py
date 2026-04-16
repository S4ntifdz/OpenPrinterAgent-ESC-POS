"""Unit tests for database module."""

from pathlib import Path

import pytest

from src.models.database import Database


class TestDatabase:
    """Tests for Database class."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Test database initialization creates parent directory."""
        db_path = tmp_path / "subdir" / "test.db"
        db = Database(db_path)

        assert db.db_path == db_path
        assert db_path.parent.exists()

    def test_init_with_string_path(self, tmp_path: Path) -> None:
        """Test database initialization with string path."""
        db_path = str(tmp_path / "test.db")
        db = Database(db_path)

        assert db.db_path == Path(db_path)

    def test_db_path_property(self, tmp_path: Path) -> None:
        """Test db_path property returns correct path."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        assert db.db_path == db_path

    def test_get_connection_context_manager(self, tmp_path: Path) -> None:
        """Test get_connection context manager yields connection."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        with db.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1 as value")
            result = cursor.fetchone()
            assert result["value"] == 1

    def test_get_cursor_context_manager_commits(self, tmp_path: Path) -> None:
        """Test get_cursor commits on success."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        with db.get_cursor() as cursor:
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            cursor.execute("INSERT INTO test VALUES (1)")

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM test")
            result = cursor.fetchall()
            assert len(result) == 1

    def test_get_cursor_context_manager_rollbacks_on_error(self, tmp_path: Path) -> None:
        """Test get_cursor rolls back on error."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        with pytest.raises(Exception):
            with db.get_cursor() as cursor:
                cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
                cursor.execute("INSERT INTO test VALUES (1)")
                raise Exception("Test error")

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM test")
            result = cursor.fetchall()
            assert len(result) == 0

    def test_init_schema_creates_tables(self, tmp_path: Path) -> None:
        """Test init_schema creates required tables."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        db.init_schema()

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row["name"] for row in cursor.fetchall()]

        assert "printers" in tables
        assert "print_jobs" in tables

    def test_init_schema_creates_indexes(self, tmp_path: Path) -> None:
        """Test init_schema creates required indexes."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        db.init_schema()

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row["name"] for row in cursor.fetchall()]

        assert "idx_print_jobs_printer_id" in indexes
        assert "idx_print_jobs_status" in indexes
        assert "idx_printers_status" in indexes

    def test_init_schema_idempotent(self, tmp_path: Path) -> None:
        """Test init_schema can be called multiple times safely."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        db.init_schema()
        db.init_schema()
        db.init_schema()

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM printers")
            result = cursor.fetchone()
            assert result["count"] == 0

    def test_context_manager_enter_exit(self, tmp_path: Path) -> None:
        """Test database as context manager."""
        db_path = tmp_path / "test.db"

        with Database(db_path) as db:
            assert db.db_path == db_path

    def test_close_is_noop(self, tmp_path: Path) -> None:
        """Test close does nothing (SQLite auto-commits)."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        db.init_schema()

        db.close()

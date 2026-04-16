"""Service container for OpenPrinterAgent GUI.

Provides a single shared instance of all services so GUI frames
can operate directly on the database without requiring the REST API.
"""

from src.models.database import Database
from src.services.job_service import JobService
from src.services.printer_service import PrinterService
from src.utils.config import get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

_container: "ServiceContainer | None" = None


class ServiceContainer:
    """Holds shared service instances for the GUI.

    Attributes:
        printer_service: Service for printer CRUD and connection management.
        job_service: Service for print job management.
    """

    def __init__(self) -> None:
        config = get_config()
        config.ensure_directories()

        self._db = Database(config.DATABASE_PATH)
        self._db.init_schema()

        self.printer_service = PrinterService(self._db)
        self.job_service = JobService(self._db)

        logger.info("ServiceContainer initialised")

    def close(self) -> None:
        """Close database connection."""
        self._db.close()


def get_services() -> ServiceContainer:
    """Return the global ServiceContainer, creating it on first call."""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container

"""Configuration management for OpenPrinterAgent.

This module provides a centralized configuration system that reads from
environment variables and provides sensible defaults.
"""

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment variables.

    Attributes:
        FLASK_ENV: Flask environment (development, production).
        FLASK_DEBUG: Enable Flask debug mode.
        API_HOST: Host to bind the API server.
        API_PORT: Port to bind the API server.
        API_SECRET_KEY: Secret key for Flask sessions.
        API_KEY: API key for authentication.
        DATABASE_URL: Database connection URL.
        DATABASE_PATH: Path to SQLite database file.
        DEFAULT_BAUDRATE: Default serial baud rate.
        DEFAULT_CONNECTION: Default connection type (usb/serial).
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR).
        LOG_FILE: Path to log file.
        CORS_ORIGINS: Comma-separated CORS allowed origins.
        BASE_DIR: Base directory of the application.
        DATA_DIR: Directory for data files.
        LOGS_DIR: Directory for log files.
    """

    FLASK_ENV: str = "development"
    FLASK_DEBUG: bool = True
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 5000
    API_SECRET_KEY: str = "dev-secret-change-me"
    API_KEY: str = "dev-api-key-change-me"
    DATABASE_URL: str = "sqlite:///data/openprinter.db"
    DATABASE_PATH: Path = field(default_factory=lambda: Path("data/openprinter.db"))
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_CONNECTION: str = "usb"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = field(default_factory=lambda: Path("logs/openprinter.log"))
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5000"
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    DATA_DIR: Path = field(init=False)
    LOGS_DIR: Path = field(init=False)

    def __post_init__(self) -> None:
        """Initialize computed fields after dataclass initialization."""
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"

    @classmethod
    def from_env(cls) -> "Config":
        """Create Config instance from environment variables.

        Returns:
            Config instance with values from environment.
        """
        import os

        return cls(
            FLASK_ENV=os.getenv("FLASK_ENV", "development"),
            FLASK_DEBUG=os.getenv("FLASK_DEBUG", "1") == "1",
            API_HOST=os.getenv("API_HOST", "127.0.0.1"),
            API_PORT=int(os.getenv("API_PORT", "5000")),
            API_SECRET_KEY=os.getenv("API_SECRET_KEY", "dev-secret-change-me"),
            API_KEY=os.getenv("API_KEY", "dev-api-key-change-me"),
            DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///data/openprinter.db"),
            DATABASE_PATH=Path(os.getenv("DATABASE_PATH", "data/openprinter.db")),
            DEFAULT_BAUDRATE=int(os.getenv("DEFAULT_BAUDRATE", "9600")),
            DEFAULT_CONNECTION=os.getenv("DEFAULT_CONNECTION", "usb"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            LOG_FILE=Path(os.getenv("LOG_FILE", "logs/openprinter.log")),
            CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5000"),
        )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as a list.

        Returns:
            List of allowed CORS origins.
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        The global Config instance.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def load_config() -> Config:
    """Load and return the application configuration.

    This function ensures directories are created and returns the config.

    Returns:
        The loaded Config instance.
    """
    config = get_config()
    config.ensure_directories()
    return config

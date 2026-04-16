"""Custom exceptions for OpenPrinterAgent."""


class OpenPrinterAgentError(Exception):
    """Base exception for all OpenPrinterAgent errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        self.message = message
        super().__init__(self.message)


class PrinterError(OpenPrinterAgentError):
    """Exception raised for printer-related errors.

    This includes invalid printer configuration, printer not found,
    or printer operation failures.
    """

    def __init__(self, message: str = "Printer error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        super().__init__(message)


class ConnectionError(OpenPrinterAgentError):
    """Exception raised for connection-related errors.

    This includes USB connection failures, serial port errors,
    or communication timeouts.
    """

    def __init__(self, message: str = "Connection error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        super().__init__(message)


class JobError(OpenPrinterAgentError):
    """Exception raised for print job-related errors.

    This includes invalid job data, job not found,
    or job processing failures.
    """

    def __init__(self, message: str = "Job error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        super().__init__(message)


class DriverError(OpenPrinterAgentError):
    """Exception raised for driver-related errors.

    This includes driver initialization failures,
    invalid driver parameters, or driver communication errors.
    """

    def __init__(self, message: str = "Driver error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        super().__init__(message)


class ConfigurationError(OpenPrinterAgentError):
    """Exception raised for configuration-related errors.

    This includes missing environment variables,
    invalid configuration values, or configuration file errors.
    """

    def __init__(self, message: str = "Configuration error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        super().__init__(message)


class ValidationError(OpenPrinterAgentError):
    """Exception raised for data validation errors.

    This includes invalid input data, schema validation failures,
    or out-of-range values.
    """

    def __init__(self, message: str = "Validation error occurred") -> None:
        """Initialize the exception.

        Args:
            message: Error description.
        """
        super().__init__(message)

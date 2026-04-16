"""Main application window for OpenPrinterAgent GUI."""

import sys
from typing import Any

import customtkinter as ctk

from src.utils.config import load_config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpenPrinterApp(ctk.CTk):
    """Main application window using CustomTkinter.

    This class creates the main application window with a tab-based
    interface for managing printers, printing, and viewing job history.
    """

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()

        self.title("OpenPrinterAgent")
        self.geometry("900x650")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._setup_services()
        self._setup_ui()
        self._setup_exception_handler()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("OpenPrinterAgent GUI started")

    def _setup_services(self) -> None:
        """Initialize the shared service container."""
        from src.gui.services import get_services
        self._services = get_services()

    def _on_closing(self) -> None:
        """Handle window closing event."""
        logger.info("Closing application...")
        if hasattr(self, "_services"):
            self._services.close()
        self.destroy()

    def _setup_ui(self) -> None:
        """Setup the user interface with tabs."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._tabview = ctk.CTkTabview(self)
        self._tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self._tabview.add("Printers")
        self._tabview.add("Print")
        self._tabview.add("Jobs")

        self._setup_printers_tab(self._tabview.tab("Printers"))
        self._setup_print_tab(self._tabview.tab("Print"))
        self._setup_jobs_tab(self._tabview.tab("Jobs"))

        # Refresh printer list when switching to the Print tab
        self._tabview.configure(command=self._on_tab_change)

        self._status_label = ctk.CTkLabel(self, text="Ready", anchor="w")
        self._status_label.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

    def _setup_printers_tab(self, parent: ctk.CTkFrame) -> None:
        """Setup the printers management tab.

        Args:
            parent: Parent frame for the tab content.
        """
        from src.gui.frames.printer_frame import PrinterFrame

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        printer_frame = PrinterFrame(parent, status_callback=self._update_status)
        printer_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _setup_print_tab(self, parent: ctk.CTkFrame) -> None:
        """Setup the print content tab.

        Args:
            parent: Parent frame for the tab content.
        """
        from src.gui.frames.print_frame import PrintFrame

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self._print_frame = PrintFrame(parent, status_callback=self._update_status)
        self._print_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _setup_jobs_tab(self, parent: ctk.CTkFrame) -> None:
        """Setup the jobs history tab.

        Args:
            parent: Parent frame for the tab content.
        """
        from src.gui.frames.jobs_frame import JobsFrame

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        jobs_frame = JobsFrame(parent, status_callback=self._update_status)
        jobs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _on_tab_change(self) -> None:
        """Called when the user switches tabs."""
        current = self._tabview.get()
        if current == "Print" and hasattr(self, "_print_frame"):
            self._print_frame.load_printers()

    def _setup_exception_handler(self) -> None:
        """Setup global exception handler for uncaught exceptions."""
        sys.excepthook = self._handle_exception

    def _handle_exception(
        self, exc_type: type, exc_value: BaseException, exc_traceback: Any
    ) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: Exception type.
            exc_value: Exception value.
            exc_traceback: Exception traceback.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        self._update_status(f"Error: {exc_value}")

        error_dialog = ctk.CTkToplevel(self)
        error_dialog.title("Error")
        error_dialog.geometry("400x150")

        ctk.CTkLabel(
            error_dialog,
            text="An error occurred:",
            font=ctk.CTkFont(weight="bold"),
        ).pack(pady=(10, 5))

        ctk.CTkLabel(error_dialog, text=str(exc_value)).pack(pady=5)

        ctk.CTkButton(error_dialog, text="OK", command=error_dialog.destroy).pack(pady=10)

    def _update_status(self, message: str) -> None:
        """Update the status label.

        Args:
            message: Status message to display.
        """
        self._status_label.configure(text=message)
        logger.info(f"Status: {message}")


def run_gui() -> None:
    """Run the GUI application."""
    load_config()
    app = OpenPrinterApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()

"""Print content frame for OpenPrinterAgent GUI."""

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from src.utils.logging import get_logger

logger = get_logger(__name__)


class PrintFrame(ctk.CTkFrame):
    """Frame for printing content.

    Uses PrinterService and JobService directly — no API server required.
    """

    def __init__(
        self, parent: ctk.CTkFrame, status_callback: Callable[[str], None], **kwargs: Any
    ) -> None:
        super().__init__(parent, **kwargs)

        self._status_callback = status_callback
        self._selected_printer_id: str | None = None
        self._printers_map: dict[str, str] = {}  # name -> id
        self._print_type = "text"

        self._setup_ui()
        self.after(100, self._load_printers)

    # ------------------------------------------------------------------ #
    # UI setup
    # ------------------------------------------------------------------ #

    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        title = ctk.CTkLabel(self, text="Print", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="w")

        printer_label = ctk.CTkLabel(self, text="Select Printer:")
        printer_label.grid(row=1, column=0, sticky="w", padx=10)

        self._printer_var = ctk.StringVar(value="Select a printer")
        self._printer_menu = ctk.CTkOptionMenu(
            self,
            variable=self._printer_var,
            values=["No printers available"],
            command=self._on_printer_select,
        )
        self._printer_menu.grid(row=1, column=1, sticky="ew", padx=(10, 5), pady=5)

        self._refresh_btn = ctk.CTkButton(
            self, text="↻", width=36, command=self._load_printers
        )
        self._refresh_btn.grid(row=1, column=2, padx=(0, 10), pady=5)

        type_label = ctk.CTkLabel(self, text="Print Type:")
        type_label.grid(row=2, column=0, sticky="w", padx=10)

        self._type_var = ctk.StringVar(value="text")
        type_frame = ctk.CTkFrame(self)
        type_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkRadioButton(
            type_frame,
            text="Text",
            variable=self._type_var,
            value="text",
            command=self._on_type_change,
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            type_frame,
            text="Barcode",
            variable=self._type_var,
            value="barcode",
            command=self._on_type_change,
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            type_frame,
            text="QR Code",
            variable=self._type_var,
            value="qrcode",
            command=self._on_type_change,
        ).pack(side="left", padx=5)

        content_label = ctk.CTkLabel(self, text="Content:")
        content_label.grid(row=3, column=0, sticky="nw", padx=10, pady=5)

        self._content_textbox = ctk.CTkTextbox(self, height=150)
        self._content_textbox.grid(row=3, column=1, columnspan=2, sticky="nsew", padx=10, pady=5)

        self._options_frame = ctk.CTkFrame(self)
        self._options_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

        self._setup_text_options()

        self._print_button = ctk.CTkButton(
            self, text="Print", command=self._send_print_job, height=40
        )
        self._print_button.grid(row=5, column=0, columnspan=3, padx=10, pady=20)

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(1, weight=1)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def load_printers(self) -> None:
        """Public method to refresh the printer list (can be called externally)."""
        self._load_printers()

    # ------------------------------------------------------------------ #
    # Private: options panels
    # ------------------------------------------------------------------ #

    def _setup_text_options(self) -> None:
        for widget in self._options_frame.winfo_children():
            widget.destroy()

        self._bold_var = ctk.BooleanVar(value=False)
        self._double_height_var = ctk.BooleanVar(value=False)
        self._double_width_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(self._options_frame, text="Bold", variable=self._bold_var).pack(
            side="left", padx=5
        )
        ctk.CTkCheckBox(
            self._options_frame, text="Double Height", variable=self._double_height_var
        ).pack(side="left", padx=5)
        ctk.CTkCheckBox(
            self._options_frame, text="Double Width", variable=self._double_width_var
        ).pack(side="left", padx=5)

    def _setup_barcode_options(self) -> None:
        for widget in self._options_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self._options_frame, text="Barcode Type:").pack(side="left", padx=5)
        self._barcode_type = ctk.CTkOptionMenu(
            self._options_frame, values=["CODE39", "CODE128", "EAN13", "UPC"]
        )
        self._barcode_type.pack(side="left", padx=5)
        self._barcode_type.set("CODE39")

    def _setup_qr_options(self) -> None:
        for widget in self._options_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self._options_frame, text="Size:").pack(side="left", padx=5)
        self._qr_size = ctk.CTkOptionMenu(
            self._options_frame, values=["3", "4", "5", "6", "7", "8", "9", "10"]
        )
        self._qr_size.pack(side="left", padx=5)
        self._qr_size.set("8")

        ctk.CTkLabel(self._options_frame, text="Error Correction:").pack(side="left", padx=5)
        self._qr_ec = ctk.CTkOptionMenu(self._options_frame, values=["L", "M", "Q", "H"])
        self._qr_ec.pack(side="left", padx=5)
        self._qr_ec.set("L")

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #

    def _on_type_change(self) -> None:
        self._print_type = self._type_var.get()
        if self._print_type == "text":
            self._setup_text_options()
        elif self._print_type == "barcode":
            self._setup_barcode_options()
        elif self._print_type == "qrcode":
            self._setup_qr_options()

    def _on_printer_select(self, name: str) -> None:
        self._selected_printer_id = self._printers_map.get(name)

    # ------------------------------------------------------------------ #
    # Load printers from service
    # ------------------------------------------------------------------ #

    def _load_printers(self) -> None:
        """Load available printers directly from the service layer."""
        from src.gui.services import get_services

        try:
            svc = get_services()
            printers = svc.printer_service.list_printers()

            if printers:
                printer_names = [p.name for p in printers]
                self._printers_map = {p.name: p.id for p in printers}
                self._printer_menu.configure(values=printer_names)
                self._printer_var.set(printer_names[0])
                self._selected_printer_id = printers[0].id
            else:
                self._printer_menu.configure(values=["No printers available"])
                self._printer_var.set("No printers available")
                self._selected_printer_id = None
                if self._status_callback:
                    self._status_callback(
                        "No printers registered — go to the Printers tab to add one"
                    )
        except Exception as e:
            logger.error(f"Failed to load printers: {e}")
            self._printer_menu.configure(values=["Error loading printers"])
            if self._status_callback:
                self._status_callback(f"Error loading printers: {e}")

    # ------------------------------------------------------------------ #
    # Send print job
    # ------------------------------------------------------------------ #

    def _send_print_job(self) -> None:
        """Send a print job directly through the service layer."""
        from src.core.entities import JobType
        from src.gui.services import get_services

        if not self._selected_printer_id:
            self._status_callback("Please select a printer first")
            return

        content = self._content_textbox.get("1.0", "end").strip()
        if not content:
            self._status_callback("Please enter content to print")
            return

        # Build content payload
        job_type: JobType
        payload: dict[str, Any] = {}

        if self._print_type == "text":
            job_type = JobType.TEXT
            payload = {
                "text": content,
                "bold": self._bold_var.get(),
                "double_height": self._double_height_var.get(),
                "double_width": self._double_width_var.get(),
            }
        elif self._print_type == "barcode":
            job_type = JobType.BARCODE
            payload = {
                "data": content,
                "barcode_type": self._barcode_type.get() if hasattr(self, "_barcode_type") else "CODE39",
            }
        elif self._print_type == "qrcode":
            job_type = JobType.QR_CODE
            payload = {
                "data": content,
                "size": int(self._qr_size.get()) if hasattr(self, "_qr_size") else 8,
                "error_correction": self._qr_ec.get() if hasattr(self, "_qr_ec") else "L",
            }
        else:
            self._status_callback("Unknown print type")
            return

        try:
            svc = get_services()

            driver = svc.printer_service.get_driver(self._selected_printer_id)
            if driver:
                # Printer is connected — print immediately
                from src.services.print_service import PrintService

                print_svc = PrintService(svc.printer_service)

                if job_type == JobType.TEXT:
                    print_svc.print_text(
                        self._selected_printer_id,
                        payload["text"],
                        bold=payload.get("bold", False),
                        double_height=payload.get("double_height", False),
                        double_width=payload.get("double_width", False),
                    )
                elif job_type == JobType.BARCODE:
                    print_svc.print_barcode(
                        self._selected_printer_id,
                        payload["data"],
                        barcode_type=payload.get("barcode_type", "CODE39"),
                    )
                elif job_type == JobType.QR_CODE:
                    print_svc.print_qrcode(
                        self._selected_printer_id,
                        payload["data"],
                        size=payload.get("size", 8),
                        error_correction=payload.get("error_correction", "L"),
                    )
                self._status_callback("Printed successfully!")
            else:
                # Printer not connected — queue the job
                job = svc.job_service.create_job(
                    printer_id=self._selected_printer_id,
                    job_type=job_type,
                    content=payload,
                )
                self._status_callback(
                    f"Job queued ({job.id[:8]}) — connect the printer first to execute it"
                )

            self._content_textbox.delete("1.0", "end")
        except Exception as e:
            logger.error(f"Failed to send print job: {e}")
            self._status_callback(f"Error: {e}")

"""Jobs history frame for OpenPrinterAgent GUI."""

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobsFrame(ctk.CTkFrame):
    """Frame for viewing job history.

    Uses JobService directly — no API server required.
    """

    def __init__(
        self, parent: ctk.CTkFrame, status_callback: Callable[[str], None], **kwargs: Any
    ) -> None:
        super().__init__(parent, **kwargs)

        self._status_callback = status_callback
        self._jobs: list[Any] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        title = ctk.CTkLabel(self, text="Job History", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(10, 10), sticky="w")

        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Filter by status:").pack(side="left", padx=5)
        self._status_filter = ctk.CTkOptionMenu(
            filter_frame,
            values=["All", "pending", "printing", "completed", "failed", "cancelled"],
            command=lambda _: self.refresh_jobs(),
        )
        self._status_filter.pack(side="left", padx=5)
        self._status_filter.set("All")

        ctk.CTkButton(filter_frame, text="Refresh", command=self.refresh_jobs).pack(
            side="left", padx=20
        )

        self._jobs_tree = ctk.CTkTextbox(self, height=350, state="disabled")
        self._jobs_tree.grid(row=2, column=0, columnspan=2, padx=10, sticky="nsew", pady=10)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        details_frame = ctk.CTkFrame(self)
        details_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(details_frame, text="Details:", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=5, pady=(5, 0)
        )

        self._details_label = ctk.CTkLabel(
            details_frame, text="Click Refresh to load jobs", justify="left", anchor="w"
        )
        self._details_label.pack(fill="x", padx=5, pady=5)

        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ctk.CTkButton(actions_frame, text="View Details", command=self._view_details).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            actions_frame, text="Cancel Selected", fg_color="orange", command=self._cancel_job
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def refresh_jobs(self) -> None:
        """Refresh the list of jobs directly from the service."""
        from src.core.entities import JobStatus
        from src.gui.services import get_services

        try:
            svc = get_services()

            status_val = self._status_filter.get()
            status_filter = None
            if status_val != "All":
                status_filter = JobStatus(status_val)

            self._jobs = svc.job_service.list_jobs(status=status_filter, limit=50)
            self._update_jobs_list()
            if self._status_callback:
                self._status_callback(f"Loaded {len(self._jobs)} jobs")
        except Exception as e:
            logger.error(f"Failed to refresh jobs: {e}")
            self._show_message(f"Error loading jobs: {e}")
            if self._status_callback:
                self._status_callback(f"Error: {e}")

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _show_message(self, message: str) -> None:
        self._jobs_tree.configure(state="normal")
        self._jobs_tree.delete("1.0", "end")
        self._jobs_tree.insert("end", f"⚠ {message}")
        self._jobs_tree.configure(state="disabled")

    def _update_jobs_list(self) -> None:
        self._jobs_tree.configure(state="normal")
        self._jobs_tree.delete("1.0", "end")

        if not self._jobs:
            self._jobs_tree.insert("end", "No jobs found.")
        else:
            header = f"{'#':<4} {'ID':<10} {'Printer':<20} {'Type':<10} {'Status':<12} {'Created':<20}\n"
            self._jobs_tree.insert("end", header)
            self._jobs_tree.insert("end", "─" * 80 + "\n")

            for i, job in enumerate(self._jobs):
                row = (
                    f"{i + 1:<4} "
                    f"{job.id[:8]:<10} "
                    f"{job.printer_id[:18]:<20} "
                    f"{job.type.value:<10} "
                    f"{job.status.value:<12} "
                    f"{str(job.created_at)[:19]:<20}\n"
                )
                self._jobs_tree.insert("end", row)

        self._jobs_tree.configure(state="disabled")

    def _view_details(self) -> None:
        if not self._jobs:
            self._status_callback("No jobs to view")
            return

        dialog = ctk.CTkInputDialog(
            text=f"Enter job number (1–{len(self._jobs)}) to view details:",
            title="View Job Details",
        )
        raw = dialog.get_input()
        if raw is None:
            return
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(self._jobs):
                job = self._jobs[idx]
                info = (
                    f"ID: {job.id}\n"
                    f"Printer: {job.printer_id}\n"
                    f"Type: {job.type.value}\n"
                    f"Status: {job.status.value}\n"
                    f"Created: {job.created_at}\n"
                    f"Error: {job.error or '—'}"
                )
                self._details_label.configure(text=info)
        except ValueError:
            self._status_callback("Invalid selection")

    def _cancel_job(self) -> None:
        if not self._jobs:
            self._status_callback("No jobs to cancel")
            return

        dialog = ctk.CTkInputDialog(
            text=f"Enter job number (1–{len(self._jobs)}) to cancel:",
            title="Cancel Job",
        )
        raw = dialog.get_input()
        if raw is None:
            return
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(self._jobs):
                from src.gui.services import get_services

                job = self._jobs[idx]
                svc = get_services()
                svc.job_service.cancel_job(job.id)
                self._status_callback(f"Job {job.id[:8]} cancelled")
                self.refresh_jobs()
        except (ValueError, Exception) as e:
            self._status_callback(f"Error: {e}")

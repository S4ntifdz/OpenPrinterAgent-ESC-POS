"""Printer management frame for OpenPrinterAgent GUI."""

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from src.core.entities import ConnectionType
from src.core.exceptions import PrinterError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PrinterFrame(ctk.CTkFrame):
    """Frame for managing printers.

    Uses PrinterService directly — no API server required.
    """

    def __init__(
        self, parent: ctk.CTkFrame, status_callback: Callable[[str], None], **kwargs: Any
    ) -> None:
        super().__init__(parent, **kwargs)

        self._status_callback = status_callback
        self._printers: list[Any] = []
        self._selected_index: int | None = None

        self._setup_ui()
        self.after(100, self.refresh_printers)

    # ------------------------------------------------------------------ #
    # UI setup
    # ------------------------------------------------------------------ #

    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        title = ctk.CTkLabel(self, text="Printers", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="w")

        self._printer_listbox = ctk.CTkTextbox(self, height=300, state="disabled")
        self._printer_listbox.grid(row=1, column=0, columnspan=2, padx=10, sticky="nsew")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ctk.CTkButton(button_frame, text="Refresh", command=self.refresh_printers).pack(
            side="left", padx=5
        )
        ctk.CTkButton(button_frame, text="Add Printer", command=self._show_add_dialog).pack(
            side="left", padx=5
        )
        ctk.CTkButton(button_frame, text="Connect", command=self._connect_selected).pack(
            side="left", padx=5
        )
        ctk.CTkButton(button_frame, text="Disconnect", command=self._disconnect_selected).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            button_frame, text="Remove", fg_color="red", command=self._remove_selected
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def refresh_printers(self) -> None:
        """Refresh the list of printers from the service."""
        from src.gui.services import get_services

        try:
            svc = get_services()
            self._printers = svc.printer_service.list_printers()
            self._update_listbox()
            if self._status_callback:
                self._status_callback(f"Printers loaded ({len(self._printers)})")
        except Exception as e:
            logger.error(f"Failed to refresh printers: {e}")
            self._show_message(f"Error loading printers: {e}")
            if self._status_callback:
                self._status_callback(f"Error: {e}")

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _update_listbox(self) -> None:
        """Update the printer listbox with current printers."""
        self._printer_listbox.configure(state="normal")
        self._printer_listbox.delete("1.0", "end")

        if not self._printers:
            self._printer_listbox.insert(
                "end",
                "No printers registered yet.\n\nClick 'Add Printer' to add your first printer.",
            )
        else:
            for i, printer in enumerate(self._printers):
                status_icon = "🟢" if printer.status.value == "connected" else "🔴"
                line = (
                    f"{i + 1}. {status_icon} {printer.name} "
                    f"[{printer.connection_type.value.upper()}] "
                    f"— {printer.status.value}\n"
                )
                self._printer_listbox.insert("end", line)

        self._printer_listbox.configure(state="disabled")

    def _show_message(self, message: str) -> None:
        self._printer_listbox.configure(state="normal")
        self._printer_listbox.delete("1.0", "end")
        self._printer_listbox.insert("end", f"⚠ {message}")
        self._printer_listbox.configure(state="disabled")

    def _get_selected_printer(self) -> Any | None:
        """Prompt user for a printer number and return that printer."""
        if not self._printers:
            self._status_callback("No printers available")
            return None

        dialog = ctk.CTkInputDialog(
            text=f"Enter printer number (1–{len(self._printers)}):",
            title="Select Printer",
        )
        raw = dialog.get_input()
        if raw is None:
            return None
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(self._printers):
                return self._printers[idx]
        except ValueError:
            pass
        self._status_callback("Invalid selection")
        return None

    # ------------------------------------------------------------------ #
    # Add dialog
    # ------------------------------------------------------------------ #

    def _show_add_dialog(self) -> None:
        """Show dialog for adding a new printer."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Printer")
        dialog.geometry("440x480")
        dialog.after(100, dialog.grab_set)

        ctk.CTkLabel(dialog, text="Printer Name:").pack(pady=(15, 0))
        name_entry = ctk.CTkEntry(dialog, width=320)
        name_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Connection Type:").pack(pady=(10, 0))
        connection_type = ctk.CTkOptionMenu(dialog, values=["USB", "Serial"], width=320)
        connection_type.pack(pady=5)
        connection_type.set("USB")

        # ----- Discovery (USB) -----
        usb_detect_label = ctk.CTkLabel(dialog, text="Detected USB Printers:")
        
        # We need entries defined before on_usb_select uses them
        vendor_label = ctk.CTkLabel(dialog, text="Vendor ID (hex, e.g. 04b8):")
        vendor_entry = ctk.CTkEntry(dialog, width=320)

        product_label = ctk.CTkLabel(dialog, text="Product ID (hex, e.g. 0202):")
        product_entry = ctk.CTkEntry(dialog, width=320)

        def on_usb_select(selection: str) -> None:
            if " - " in selection:
                vid, pid = selection.split(" - ")[0].split(":")
                vendor_entry.delete(0, "end")
                vendor_entry.insert(0, vid)
                product_entry.delete(0, "end")
                product_entry.insert(0, pid)

        usb_devices = self._scan_usb_printers()
        usb_detect_menu = ctk.CTkOptionMenu(
            dialog, 
            values=usb_devices if usb_devices else ["No USB printers detected"],
            width=320,
            command=on_usb_select
        )

        # ----- Serial fields -----
        port_label = ctk.CTkLabel(dialog, text="Serial Port (e.g. /dev/ttyUSB0):")
        port_entry = ctk.CTkEntry(dialog, width=320)

        baud_label = ctk.CTkLabel(dialog, text="Baud Rate:")
        baud_entry = ctk.CTkEntry(dialog, width=320)
        baud_entry.insert(0, "9600")

        # Define update_fields AFTER all widgets are defined
        def update_fields(*_: Any) -> None:
            if connection_type.get() == "USB":
                port_label.pack_forget()
                port_entry.pack_forget()
                baud_label.pack_forget()
                baud_entry.pack_forget()
                
                usb_detect_label.pack(pady=(10, 0))
                usb_detect_menu.pack(pady=5)
                vendor_label.pack(pady=(10, 0))
                vendor_entry.pack(pady=5)
                product_label.pack(pady=(10, 0))
                product_entry.pack(pady=5)
            else:
                usb_detect_label.pack_forget()
                usb_detect_menu.pack_forget()
                vendor_label.pack_forget()
                vendor_entry.pack_forget()
                product_label.pack_forget()
                product_entry.pack_forget()
                
                port_label.pack(pady=(10, 0))
                port_entry.pack(pady=5)
                baud_label.pack(pady=(10, 0))
                baud_entry.pack(pady=5)

        connection_type.configure(command=update_fields)
        update_fields()

        def add_printer() -> None:
            from src.gui.services import get_services

            name = name_entry.get().strip()
            if not name:
                self._status_callback("Printer name is required")
                return

            conn = ConnectionType(connection_type.get().lower())
            kwargs: dict[str, Any] = {"name": name, "connection_type": conn}

            if conn == ConnectionType.USB:
                try:
                    kwargs["vendor_id"] = int(vendor_entry.get().strip(), 16)
                    kwargs["product_id"] = int(product_entry.get().strip(), 16)
                except ValueError:
                    self._status_callback("Invalid Vendor/Product ID — must be hex (e.g. 04b8)")
                    return
            else:
                port = port_entry.get().strip()
                if not port:
                    self._status_callback("Serial port is required")
                    return
                kwargs["port"] = port
                try:
                    kwargs["baudrate"] = int(baud_entry.get().strip())
                except ValueError:
                    kwargs["baudrate"] = 9600

            try:
                svc = get_services()
                printer = svc.printer_service.add_printer(**kwargs)
                self._status_callback(f"Printer '{printer.name}' added")
                dialog.destroy()
                self.refresh_printers()
            except Exception as e:
                logger.error(f"Failed to add printer: {e}")
                self._status_callback(f"Error: {e}")

        ctk.CTkButton(dialog, text="Add Printer", command=add_printer).pack(pady=20)

    def _scan_usb_printers(self) -> list[str]:
        """Scan for connected USB printers using pyusb."""
        import usb.core
        import usb.util
        
        printers = []
        try:
            # Find devices with printer class (0x07)
            devices = usb.core.find(find_all=True)
            for dev in devices:
                # Some printers don't report as class 0x07 at the device level,
                # we also check the interface level
                is_printer = (dev.bDeviceClass == 7)
                if not is_printer:
                    for cfg in dev:
                        for intf in cfg:
                            if intf.bInterfaceClass == 7:
                                is_printer = True
                                break
                
                if is_printer:
                    vid = f"{dev.idVendor:04x}"
                    pid = f"{dev.idProduct:04x}"
                    try:
                        mfr = usb.util.get_string(dev, dev.iManufacturer) or "Unknown"
                        prod = usb.util.get_string(dev, dev.iProduct) or "Printer"
                        printers.append(f"{vid}:{pid} - {mfr} {prod}")
                    except:
                        printers.append(f"{vid}:{pid} - USB Printer")
        except Exception as e:
            logger.warning(f"USB scan failed: {e}")
            
        return printers

    # ------------------------------------------------------------------ #
    # Connect / Disconnect / Remove
    # ------------------------------------------------------------------ #

    def _connect_selected(self) -> None:
        printer = self._get_selected_printer()
        if printer is None:
            return
        from src.gui.services import get_services

        try:
            svc = get_services()
            svc.printer_service.connect_printer(printer.id)
            self._status_callback(f"Connected: {printer.name}")
            self.refresh_printers()
        except PrinterError as e:
            self._status_callback(f"Connect failed: {e}")

    def _disconnect_selected(self) -> None:
        printer = self._get_selected_printer()
        if printer is None:
            return
        from src.gui.services import get_services

        try:
            svc = get_services()
            svc.printer_service.disconnect_printer(printer.id)
            self._status_callback(f"Disconnected: {printer.name}")
            self.refresh_printers()
        except PrinterError as e:
            self._status_callback(f"Disconnect failed: {e}")

    def _remove_selected(self) -> None:
        printer = self._get_selected_printer()
        if printer is None:
            return
        from src.gui.services import get_services

        try:
            svc = get_services()
            svc.printer_service.remove_printer(printer.id)
            self._status_callback(f"Removed: {printer.name}")
            self.refresh_printers()
        except PrinterError as e:
            self._status_callback(f"Remove failed: {e}")

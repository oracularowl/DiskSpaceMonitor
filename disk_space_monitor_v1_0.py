"""
Disk Space Monitor v1.0

Change comments:
- v1.0: Added a Python Tkinter GUI for monitoring free disk space.
- v1.0: Added disk selection so the user can choose which drive to monitor.
- v1.0: Added threshold mode selection for percent free space or size free space.
- v1.0: Added foreground popup alerts when the selected disk reaches the threshold.
- v1.0: Added start/stop monitoring controls and live disk-space status updates.
- v1.0: Added repeated interval checks so monitoring continues after the first check.
- v1.0: Created this script as a versioned file so any future original file is not overwritten.
"""

import ctypes
import shutil
import string
import tkinter as tk
from tkinter import messagebox, ttk


APP_TITLE = "Disk Space Monitor v1.0"
DEFAULT_CHECK_INTERVAL_SECONDS = 30


# Change: This helper discovers Windows drive letters for the disk selection feature.
def get_available_drives():
    """Return available Windows drive letters such as C:\\ and D:\\."""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()

    for index, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << index):
            drive = f"{letter}:\\"
            try:
                shutil.disk_usage(drive)
            except OSError:
                continue
            drives.append(drive)

    return drives


# Change: This helper converts byte counts into readable units for the GUI and popup.
def format_bytes(byte_count):
    """Convert bytes to a compact human-readable value."""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(byte_count)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{byte_count} B"


class DiskSpaceMonitorApp:
    """Tkinter GUI application for monitoring disk free space."""

    # Change: Initialize all GUI state in one place so the program starts cleanly.
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("560x430")
        self.root.minsize(520, 400)

        self.monitoring = False
        self.after_id = None
        self.alert_active = False

        self.selected_drive = tk.StringVar()
        self.threshold_mode = tk.StringVar(value="percent")
        self.threshold_value = tk.StringVar(value="10")
        self.check_interval = tk.StringVar(value=str(DEFAULT_CHECK_INTERVAL_SECONDS))
        self.status_text = tk.StringVar(value="Select a disk and start monitoring.")

        self.drives = get_available_drives()
        if self.drives:
            self.selected_drive.set(self.drives[0])

        self.build_gui()
        self.refresh_status()

    # Change: Build the main GUI with disk, threshold, interval, and control sections.
    def build_gui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Monitor a selected disk and show a foreground popup when free space is low.",
            wraplength=500,
        )
        subtitle.pack(anchor="w", pady=(4, 16))

        settings = ttk.LabelFrame(main, text="Monitor Settings", padding=12)
        settings.pack(fill=tk.X)

        ttk.Label(settings, text="Disk to monitor").grid(row=0, column=0, sticky="w")
        self.drive_combo = ttk.Combobox(
            settings,
            textvariable=self.selected_drive,
            values=self.drives,
            state="readonly",
            width=18,
        )
        self.drive_combo.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=4)
        self.drive_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_status())

        refresh_button = ttk.Button(settings, text="Refresh Disks", command=self.refresh_drives)
        refresh_button.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=4)

        ttk.Label(settings, text="Threshold type").grid(row=1, column=0, sticky="w")
        threshold_type_frame = ttk.Frame(settings)
        threshold_type_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=(12, 0), pady=4)

        percent_radio = ttk.Radiobutton(
            threshold_type_frame,
            text="Percent free",
            variable=self.threshold_mode,
            value="percent",
            command=self.refresh_status,
        )
        percent_radio.pack(side=tk.LEFT)

        size_radio = ttk.Radiobutton(
            threshold_type_frame,
            text="Size free (GB)",
            variable=self.threshold_mode,
            value="size",
            command=self.refresh_status,
        )
        size_radio.pack(side=tk.LEFT, padx=(16, 0))

        ttk.Label(settings, text="Threshold value").grid(row=2, column=0, sticky="w")
        threshold_entry = ttk.Entry(settings, textvariable=self.threshold_value, width=20)
        threshold_entry.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=4)

        ttk.Label(settings, text="Check every seconds").grid(row=3, column=0, sticky="w")
        interval_entry = ttk.Entry(settings, textvariable=self.check_interval, width=20)
        interval_entry.grid(row=3, column=1, sticky="ew", padx=(12, 0), pady=4)

        settings.columnconfigure(1, weight=1)

        status_frame = ttk.LabelFrame(main, text="Current Disk Status", padding=12)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(14, 0))

        self.status_label = ttk.Label(status_frame, textvariable=self.status_text, justify=tk.LEFT)
        self.status_label.pack(anchor="w", fill=tk.X)

        self.progress = ttk.Progressbar(status_frame, maximum=100, value=0)
        self.progress.pack(fill=tk.X, pady=(12, 0))

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(14, 0))

        self.start_button = ttk.Button(buttons, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = ttk.Button(
            buttons,
            text="Stop Monitoring",
            command=self.stop_monitoring,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=(8, 0))

        self.check_now_button = ttk.Button(buttons, text="Check Now", command=self.check_disk_space)
        self.check_now_button.pack(side=tk.LEFT, padx=(8, 0))

        quit_button = ttk.Button(buttons, text="Quit", command=self.on_close)
        quit_button.pack(side=tk.RIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # Change: Refresh drive choices without restarting the program.
    def refresh_drives(self):
        current_drive = self.selected_drive.get()
        self.drives = get_available_drives()
        self.drive_combo.configure(values=self.drives)

        if current_drive in self.drives:
            self.selected_drive.set(current_drive)
        elif self.drives:
            self.selected_drive.set(self.drives[0])
        else:
            self.selected_drive.set("")

        self.refresh_status()

    # Change: Validate user settings before monitoring starts or checks run.
    def validate_settings(self):
        drive = self.selected_drive.get()
        if not drive:
            messagebox.showerror("Missing Disk", "Select a disk to monitor.")
            return None

        try:
            threshold = float(self.threshold_value.get())
        except ValueError:
            messagebox.showerror("Invalid Threshold", "Enter a valid number for the threshold.")
            return None

        if threshold < 0:
            messagebox.showerror("Invalid Threshold", "Threshold must be zero or higher.")
            return None

        if self.threshold_mode.get() == "percent" and threshold > 100:
            messagebox.showerror("Invalid Threshold", "Percent threshold must be 100 or lower.")
            return None

        try:
            interval = int(float(self.check_interval.get()))
        except ValueError:
            messagebox.showerror("Invalid Interval", "Enter a valid number of seconds.")
            return None

        if interval < 1:
            messagebox.showerror("Invalid Interval", "Check interval must be at least 1 second.")
            return None

        return drive, threshold, interval

    # Change: Start timed monitoring and update buttons to show the active state.
    def start_monitoring(self):
        settings = self.validate_settings()
        if settings is None:
            return

        self.monitoring = True
        self.alert_active = False
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.schedule_next_check(run_now=True)

    # Change: Stop timed monitoring and cancel any pending scheduled check.
    def stop_monitoring(self):
        self.monitoring = False
        self.alert_active = False

        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_text.set("Monitoring stopped.")

    # Change: Schedule repeated checks using Tkinter's event loop instead of a background thread.
    def schedule_next_check(self, run_now=False):
        if not self.monitoring:
            return

        if run_now or self.after_id is not None:
            self.check_disk_space()

        settings = self.validate_settings()
        if settings is None:
            self.stop_monitoring()
            return

        _drive, _threshold, interval = settings
        self.after_id = self.root.after(interval * 1000, self.schedule_next_check)

    # Change: Read disk usage and compare free space against percent or size threshold.
    def check_disk_space(self):
        settings = self.validate_settings()
        if settings is None:
            return

        drive, threshold, _interval = settings

        try:
            total, used, free = shutil.disk_usage(drive)
        except OSError as error:
            messagebox.showerror("Disk Error", f"Could not read disk {drive}\n\n{error}")
            if self.monitoring:
                self.stop_monitoring()
            return

        free_percent = (free / total) * 100 if total else 0
        used_percent = (used / total) * 100 if total else 0
        self.progress.configure(value=used_percent)

        mode = self.threshold_mode.get()
        if mode == "percent":
            threshold_reached = free_percent <= threshold
            threshold_description = f"{threshold:.2f}% free"
        else:
            threshold_bytes = threshold * 1024 * 1024 * 1024
            threshold_reached = free <= threshold_bytes
            threshold_description = f"{threshold:.2f} GB free"

        self.status_text.set(
            f"Disk: {drive}\n"
            f"Total: {format_bytes(total)}\n"
            f"Used: {format_bytes(used)} ({used_percent:.2f}%)\n"
            f"Free: {format_bytes(free)} ({free_percent:.2f}%)\n"
            f"Alert threshold: {threshold_description}"
        )

        if threshold_reached:
            self.show_foreground_alert(drive, free, free_percent, threshold_description)
        else:
            self.alert_active = False

    # Change: Update status without forcing validation popups during normal GUI changes.
    def refresh_status(self):
        drive = self.selected_drive.get()
        if not drive:
            self.status_text.set("No available disks found.")
            self.progress.configure(value=0)
            return

        try:
            total, used, free = shutil.disk_usage(drive)
        except OSError as error:
            self.status_text.set(f"Could not read disk {drive}: {error}")
            self.progress.configure(value=0)
            return

        used_percent = (used / total) * 100 if total else 0
        free_percent = (free / total) * 100 if total else 0
        self.progress.configure(value=used_percent)
        self.status_text.set(
            f"Disk: {drive}\n"
            f"Total: {format_bytes(total)}\n"
            f"Used: {format_bytes(used)} ({used_percent:.2f}%)\n"
            f"Free: {format_bytes(free)} ({free_percent:.2f}%)"
        )

    # Change: Use topmost window behavior so the threshold warning appears in the foreground.
    def show_foreground_alert(self, drive, free_bytes, free_percent, threshold_description):
        if self.alert_active:
            return

        self.alert_active = True
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()

        messagebox.showwarning(
            "Disk Space Threshold Reached",
            f"Disk {drive} has reached the free-space threshold.\n\n"
            f"Current free space: {format_bytes(free_bytes)} ({free_percent:.2f}%)\n"
            f"Threshold: {threshold_description}",
            parent=self.root,
        )

        self.root.attributes("-topmost", False)

    # Change: Cleanly stop monitoring before the application exits.
    def on_close(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.root.destroy()


# Change: Standard application entry point keeps this file import-safe.
def main():
    root = tk.Tk()
    app = DiskSpaceMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

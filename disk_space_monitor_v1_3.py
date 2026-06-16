"""
Disk Space Monitor v1.3

Change comments:
- v1.0: Added a Python Tkinter GUI for monitoring free disk space.
- v1.0: Added disk selection so the user can choose which drive to monitor.
- v1.0: Added threshold mode selection for percent free space or size free space.
- v1.0: Added foreground popup alerts when the selected disk reaches the threshold.
- v1.0: Added start/stop monitoring controls and live disk-space status updates.
- v1.0: Added repeated interval checks so monitoring continues after the first check.
- v1.0: Created this script as a versioned file so any future original file is not overwritten.
- v1.1: Reworked the automatic refresh loop so every scheduled interval checks disk space.
- v1.1: Added a dedicated topmost popup window for more reliable foreground alerts.
- v1.1: Added last-check and next-check status text so automatic refresh is visible.
- v1.1: Reset the alert trigger when monitor settings change or free space recovers.
- v1.2: Added an always-on display refresh timer so disk status updates automatically.
- v1.2: Added threshold YES/NO information to the normal status view before monitoring starts.
- v1.2: Increased the window height and moved controls so Start Monitoring remains visible.
- v1.2: Split display refresh from popup monitoring so the screen updates even when alerts are stopped.
- v1.3: Added 7-Zip process detection for currently running extract/compress jobs.
- v1.3: Added Pause 7-Zip and Resume 7-Zip buttons using Windows suspend/resume APIs.
- v1.3: Added a 7-Zip process dropdown and refresh button so the user can choose the active process.
- v1.3: Kept the disk monitor behavior and all previous change comments while adding process controls.
"""

import ctypes
import ctypes.wintypes
import csv
import shutil
import string
import subprocess
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk


APP_TITLE = "Disk Space Monitor v1.3"
DEFAULT_CHECK_INTERVAL_SECONDS = 30
DISPLAY_REFRESH_SECONDS = 5
SEVEN_ZIP_PROCESS_NAMES = {"7z.exe", "7za.exe", "7zr.exe", "7zg.exe"}
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

ctypes.windll.kernel32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
ctypes.windll.kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
ctypes.windll.kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
ctypes.windll.kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
ctypes.windll.ntdll.NtSuspendProcess.argtypes = [ctypes.wintypes.HANDLE]
ctypes.windll.ntdll.NtSuspendProcess.restype = ctypes.c_long
ctypes.windll.ntdll.NtResumeProcess.argtypes = [ctypes.wintypes.HANDLE]
ctypes.windll.ntdll.NtResumeProcess.restype = ctypes.c_long


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


# Change: This helper centralizes disk readings so GUI refresh and monitoring match.
def read_disk_usage(drive):
    """Return disk usage details for one selected drive."""
    total, used, free = shutil.disk_usage(drive)
    used_percent = (used / total) * 100 if total else 0
    free_percent = (free / total) * 100 if total else 0
    return total, used, free, used_percent, free_percent


# Change: This helper lists active 7-Zip command/GUI processes for pause/resume controls.
def get_7zip_processes():
    """Return running 7-Zip process display strings mapped to process IDs."""
    processes = []

    try:
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return processes

    for row in csv.reader(output.splitlines()):
        if len(row) < 2:
            continue

        image_name = row[0].strip()
        pid_text = row[1].strip()
        if image_name.lower() not in SEVEN_ZIP_PROCESS_NAMES:
            continue

        try:
            pid = int(pid_text)
        except ValueError:
            continue

        display = f"{image_name} - PID {pid}"

        processes.append({"display": display, "pid": pid, "name": image_name})

    return processes


# Change: This helper opens a process handle with suspend/resume permissions.
def open_process_for_suspend_resume(pid):
    """Open a Windows process handle that can be suspended or resumed."""
    access = PROCESS_SUSPEND_RESUME | PROCESS_QUERY_LIMITED_INFORMATION
    handle = ctypes.windll.kernel32.OpenProcess(access, False, int(pid))
    if not handle:
        raise ctypes.WinError()
    return handle


# Change: This helper pauses a selected 7-Zip process without terminating it.
def suspend_process(pid):
    """Suspend a process by PID using NtSuspendProcess."""
    handle = open_process_for_suspend_resume(pid)
    try:
        result = ctypes.windll.ntdll.NtSuspendProcess(handle)
        if result != 0:
            raise OSError(f"NtSuspendProcess failed with status {result}")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


# Change: This helper resumes a selected 7-Zip process after it was paused.
def resume_process(pid):
    """Resume a process by PID using NtResumeProcess."""
    handle = open_process_for_suspend_resume(pid)
    try:
        result = ctypes.windll.ntdll.NtResumeProcess(handle)
        if result != 0:
            raise OSError(f"NtResumeProcess failed with status {result}")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


class DiskSpaceMonitorApp:
    """Tkinter GUI application for monitoring disk free space."""

    # Change: Initialize all GUI state in one place so the program starts cleanly.
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("660x700")
        self.root.minsize(620, 650)

        self.monitoring = False
        self.after_id = None
        self.display_after_id = None
        self.alert_shown_for_current_threshold = False
        self.alert_window = None

        self.selected_drive = tk.StringVar()
        self.threshold_mode = tk.StringVar(value="percent")
        self.threshold_value = tk.StringVar(value="10")
        self.check_interval = tk.StringVar(value=str(DEFAULT_CHECK_INTERVAL_SECONDS))
        self.status_text = tk.StringVar(value="Select a disk and start monitoring.")
        self.selected_7zip_process = tk.StringVar()
        self.seven_zip_status_text = tk.StringVar(value="No 7-Zip process selected.")
        self.seven_zip_processes = []

        self.drives = get_available_drives()
        if self.drives:
            self.selected_drive.set(self.drives[0])

        self.build_gui()
        self.refresh_7zip_processes(show_message=False)
        self.refresh_status()
        self.schedule_display_refresh()

    # Change: Build the main GUI with disk, threshold, interval, and control sections.
    def build_gui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Monitor a selected disk and show a foreground popup when free space is low.",
            wraplength=530,
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
        self.drive_combo.bind("<<ComboboxSelected>>", lambda _event: self.settings_changed())

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
            command=self.settings_changed,
        )
        percent_radio.pack(side=tk.LEFT)

        size_radio = ttk.Radiobutton(
            threshold_type_frame,
            text="Size free (GB)",
            variable=self.threshold_mode,
            value="size",
            command=self.settings_changed,
        )
        size_radio.pack(side=tk.LEFT, padx=(16, 0))

        ttk.Label(settings, text="Threshold value").grid(row=2, column=0, sticky="w")
        threshold_entry = ttk.Entry(settings, textvariable=self.threshold_value, width=20)
        threshold_entry.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=4)
        threshold_entry.bind("<KeyRelease>", lambda _event: self.alert_reset_only())

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

        self.check_now_button = ttk.Button(buttons, text="Check Now", command=self.check_now)
        self.check_now_button.pack(side=tk.LEFT, padx=(8, 0))

        quit_button = ttk.Button(buttons, text="Quit", command=self.on_close)
        quit_button.pack(side=tk.RIGHT)

        seven_zip_frame = ttk.LabelFrame(main, text="7-Zip Extract Process", padding=12)
        seven_zip_frame.pack(fill=tk.X, pady=(14, 0))

        # Change: Add controls for choosing and controlling a currently running 7-Zip process.
        ttk.Label(seven_zip_frame, text="Running 7-Zip process").grid(row=0, column=0, sticky="w")
        self.seven_zip_combo = ttk.Combobox(
            seven_zip_frame,
            textvariable=self.selected_7zip_process,
            values=[],
            state="readonly",
            width=38,
        )
        self.seven_zip_combo.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=4)

        refresh_7zip_button = ttk.Button(
            seven_zip_frame,
            text="Refresh 7-Zip",
            command=lambda: self.refresh_7zip_processes(show_message=True),
        )
        refresh_7zip_button.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=4)

        pause_button = ttk.Button(seven_zip_frame, text="Pause 7-Zip", command=self.pause_selected_7zip)
        pause_button.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=4)

        resume_button = ttk.Button(seven_zip_frame, text="Resume 7-Zip", command=self.resume_selected_7zip)
        resume_button.grid(row=1, column=1, sticky="e", pady=4)

        seven_zip_status = ttk.Label(
            seven_zip_frame,
            textvariable=self.seven_zip_status_text,
            justify=tk.LEFT,
            wraplength=580,
        )
        seven_zip_status.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        seven_zip_frame.columnconfigure(1, weight=1)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # Change: Reset the alert state and refresh status after setting changes.
    def settings_changed(self):
        self.alert_reset_only()
        self.refresh_status()

    # Change: Reset the alert state without forcing validation popups while typing.
    def alert_reset_only(self):
        self.alert_shown_for_current_threshold = False

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

        self.settings_changed()

    # Change: Refresh the list of active 7-Zip processes without disturbing disk monitoring.
    def refresh_7zip_processes(self, show_message=False):
        current_selection = self.selected_7zip_process.get()
        self.seven_zip_processes = get_7zip_processes()
        process_names = [process["display"] for process in self.seven_zip_processes]
        self.seven_zip_combo.configure(values=process_names)

        if current_selection in process_names:
            self.selected_7zip_process.set(current_selection)
        elif process_names:
            self.selected_7zip_process.set(process_names[0])
        else:
            self.selected_7zip_process.set("")

        if process_names:
            self.seven_zip_status_text.set(f"Found {len(process_names)} running 7-Zip process(es).")
        else:
            self.seven_zip_status_text.set("No running 7-Zip process found. Start an extraction, then click Refresh 7-Zip.")
            if show_message:
                messagebox.showinfo("No 7-Zip Process", "No running 7-Zip process was found.")

    # Change: Find the selected 7-Zip process so pause/resume targets the intended PID.
    def get_selected_7zip_process(self):
        selected = self.selected_7zip_process.get()
        for process in self.seven_zip_processes:
            if process["display"] == selected:
                return process

        messagebox.showerror("No Process Selected", "Select a running 7-Zip process first.")
        return None

    # Change: Pause the chosen 7-Zip extract process without closing it.
    def pause_selected_7zip(self):
        self.refresh_7zip_processes(show_message=False)
        process = self.get_selected_7zip_process()
        if process is None:
            return

        try:
            suspend_process(process["pid"])
        except OSError as error:
            messagebox.showerror(
                "Pause Failed",
                f"Could not pause {process['display']}.\n\n"
                f"Try running this app as Administrator if 7-Zip was started with higher privileges.\n\n"
                f"{error}",
            )
            return

        self.seven_zip_status_text.set(f"Paused {process['display']}. Click Resume 7-Zip to continue it.")

    # Change: Resume the chosen 7-Zip process after it was paused.
    def resume_selected_7zip(self):
        process = self.get_selected_7zip_process()
        if process is None:
            return

        try:
            resume_process(process["pid"])
        except OSError as error:
            messagebox.showerror(
                "Resume Failed",
                f"Could not resume {process['display']}.\n\n"
                f"Try running this app as Administrator if 7-Zip was started with higher privileges.\n\n"
                f"{error}",
            )
            return

        self.seven_zip_status_text.set(f"Resumed {process['display']}.")
        self.refresh_7zip_processes(show_message=False)

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

        self.cancel_scheduled_check()
        self.monitoring = True
        self.alert_shown_for_current_threshold = False
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.run_monitor_check()

    # Change: Stop timed monitoring and cancel any pending scheduled check.
    def stop_monitoring(self):
        self.monitoring = False
        self.alert_shown_for_current_threshold = False
        self.cancel_scheduled_check()
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.refresh_status()

    # Change: Cancel a scheduled Tkinter timer safely before replacing or exiting it.
    def cancel_scheduled_check(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    # Change: Run the actual monitor check on every timer tick, then schedule the next tick.
    def run_monitor_check(self):
        if not self.monitoring:
            return

        self.after_id = None
        settings = self.validate_settings()
        if settings is None:
            self.stop_monitoring()
            return

        _drive, _threshold, interval = settings
        self.check_disk_space(show_alert=True, schedule_text_seconds=interval)

        if self.monitoring:
            self.after_id = self.root.after(interval * 1000, self.run_monitor_check)

    # Change: Let the Check Now button use the same threshold logic as automatic monitoring.
    def check_now(self):
        self.check_disk_space(show_alert=True)

    # Change: Refresh the visible disk status automatically even when popup monitoring is stopped.
    def schedule_display_refresh(self):
        self.display_after_id = None
        self.refresh_status()
        self.display_after_id = self.root.after(DISPLAY_REFRESH_SECONDS * 1000, self.schedule_display_refresh)

    # Change: Read disk usage and compare free space against percent or size threshold.
    def check_disk_space(self, show_alert=False, schedule_text_seconds=None):
        settings = self.validate_settings()
        if settings is None:
            return

        drive, threshold, _interval = settings

        try:
            total, used, free, used_percent, free_percent = read_disk_usage(drive)
        except OSError as error:
            messagebox.showerror("Disk Error", f"Could not read disk {drive}\n\n{error}")
            if self.monitoring:
                self.stop_monitoring()
            return

        self.progress.configure(value=used_percent)

        mode = self.threshold_mode.get()
        if mode == "percent":
            threshold_reached = free_percent <= threshold
            threshold_description = f"{threshold:.2f}% free"
        else:
            threshold_bytes = threshold * 1024 * 1024 * 1024
            threshold_reached = free <= threshold_bytes
            threshold_description = f"{threshold:.2f} GB free"

        if not threshold_reached:
            self.alert_shown_for_current_threshold = False

        status_lines = [
            f"Disk: {drive}",
            f"Total: {format_bytes(total)}",
            f"Used: {format_bytes(used)} ({used_percent:.2f}%)",
            f"Free: {format_bytes(free)} ({free_percent:.2f}%)",
            f"Alert threshold: {threshold_description}",
            f"Threshold reached: {'YES' if threshold_reached else 'NO'}",
            f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.monitoring and schedule_text_seconds:
            next_check = datetime.now() + timedelta(seconds=schedule_text_seconds)
            status_lines.append(f"Next check: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")

        self.status_text.set("\n".join(status_lines))

        if show_alert and threshold_reached and not self.alert_shown_for_current_threshold:
            self.alert_shown_for_current_threshold = True
            self.show_foreground_alert(drive, free, free_percent, threshold_description)

    # Change: Update status without forcing validation popups during normal GUI changes.
    def refresh_status(self):
        drive = self.selected_drive.get()
        if not drive:
            self.status_text.set("No available disks found.")
            self.progress.configure(value=0)
            return

        try:
            total, used, free, used_percent, free_percent = read_disk_usage(drive)
        except OSError as error:
            self.status_text.set(f"Could not read disk {drive}: {error}")
            self.progress.configure(value=0)
            return

        threshold_text = "Invalid threshold"
        threshold_reached = "Unknown"

        try:
            threshold = float(self.threshold_value.get())
            if self.threshold_mode.get() == "percent":
                threshold_text = f"{threshold:.2f}% free"
                threshold_reached = "YES" if free_percent <= threshold else "NO"
            else:
                threshold_text = f"{threshold:.2f} GB free"
                threshold_bytes = threshold * 1024 * 1024 * 1024
                threshold_reached = "YES" if free <= threshold_bytes else "NO"
        except ValueError:
            pass

        monitor_state = "ON" if self.monitoring else "OFF"

        self.progress.configure(value=used_percent)
        self.status_text.set(
            f"Disk: {drive}\n"
            f"Total: {format_bytes(total)}\n"
            f"Used: {format_bytes(used)} ({used_percent:.2f}%)\n"
            f"Free: {format_bytes(free)} ({free_percent:.2f}%)\n"
            f"Alert threshold: {threshold_text}\n"
            f"Threshold reached: {threshold_reached}\n"
            f"Popup monitoring: {monitor_state}\n"
            f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Display auto-refresh: every {DISPLAY_REFRESH_SECONDS} seconds"
        )

    # Change: Use a dedicated topmost window so the threshold warning reliably appears in front.
    def show_foreground_alert(self, drive, free_bytes, free_percent, threshold_description):
        if self.alert_window is not None and self.alert_window.winfo_exists():
            self.alert_window.lift()
            self.alert_window.focus_force()
            return

        alert = tk.Toplevel(self.root)
        self.alert_window = alert
        alert.title("Disk Space Threshold Reached")
        alert.geometry("430x220")
        alert.resizable(False, False)
        alert.attributes("-topmost", True)
        alert.transient(self.root)

        frame = ttk.Frame(alert, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)

        heading = ttk.Label(frame, text="Disk space threshold reached", font=("Segoe UI", 12, "bold"))
        heading.pack(anchor="w")

        details = ttk.Label(
            frame,
            text=(
                f"Disk {drive} has reached the free-space threshold.\n\n"
                f"Current free space: {format_bytes(free_bytes)} ({free_percent:.2f}%)\n"
                f"Threshold: {threshold_description}"
            ),
            justify=tk.LEFT,
            wraplength=380,
        )
        details.pack(anchor="w", fill=tk.X, pady=(12, 14))

        ok_button = ttk.Button(alert, text="OK", command=alert.destroy)
        ok_button.pack(pady=(0, 16))

        alert.protocol("WM_DELETE_WINDOW", alert.destroy)
        alert.update_idletasks()

        screen_width = alert.winfo_screenwidth()
        screen_height = alert.winfo_screenheight()
        x = max((screen_width - alert.winfo_width()) // 2, 0)
        y = max((screen_height - alert.winfo_height()) // 2, 0)
        alert.geometry(f"+{x}+{y}")

        self.root.lift()
        alert.lift()
        alert.focus_force()
        alert.after(500, lambda: alert.attributes("-topmost", False) if alert.winfo_exists() else None)

    # Change: Cleanly stop monitoring before the application exits.
    def on_close(self):
        self.monitoring = False
        self.cancel_scheduled_check()
        if self.display_after_id is not None:
            self.root.after_cancel(self.display_after_id)
            self.display_after_id = None
        self.root.destroy()


# Change: Standard application entry point keeps this file import-safe.
def main():
    root = tk.Tk()
    DiskSpaceMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

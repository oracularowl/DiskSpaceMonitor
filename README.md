# Disk Space Monitor

A Windows desktop utility for monitoring free disk space from a simple Python Tkinter GUI.

The app lets you select a drive, set a low-free-space threshold, watch live usage status, and show a foreground popup when the selected drive reaches the configured threshold. Version 1.3 also includes controls to pause and resume a currently running 7-Zip extraction process.

## Current Version

Current source version: `disk_space_monitor_v1_3.py`

Current standalone executable: `dist/DiskSpaceMonitor_v1_3.exe`

## Features

- Select a Windows drive to monitor, such as `C:\`, `D:\`, or removable drives.
- Set the alert threshold by:
  - Percent free space
  - Free space size in GB
- Live disk status display:
  - Total space
  - Used space
  - Free space
  - Threshold value
  - Threshold reached status
  - Popup monitoring status
  - Last refresh time
- Automatic display refresh every 5 seconds.
- Start and stop popup monitoring.
- Manual `Check Now` button.
- Foreground popup alert when free space reaches the configured threshold.
- Versioned source files so previous versions are not overwritten.
- 7-Zip process controls:
  - Detect running `7z.exe`, `7za.exe`, `7zr.exe`, and `7zG.exe` processes.
  - Pause a selected running 7-Zip process.
  - Resume a selected paused 7-Zip process.

## Screens and Controls

### Monitor Settings

Use this section to choose the disk and threshold.

- `Disk to monitor`: Select the drive letter to watch.
- `Refresh Disks`: Reload available drives.
- `Threshold type`: Choose percent free or size free in GB.
- `Threshold value`: Enter the alert value.
- `Check every seconds`: Set how often popup monitoring checks the disk.

### Current Disk Status

This section refreshes automatically every 5 seconds and shows whether the threshold is currently reached.

Example:

```text
Disk: A:\
Total: 4.55 TB
Used: 4.41 TB (97.00%)
Free: 139.62 GB (3.00%)
Alert threshold: 10.00% free
Threshold reached: YES
Popup monitoring: OFF
Last refreshed: 2026-06-16 17:20:00
Display auto-refresh: every 5 seconds
```

If `Threshold reached` says `YES`, click `Start Monitoring` to enable popup alerts.

### 7-Zip Extract Process

Use this section when a 7-Zip extraction is already running and you want to pause it temporarily.

1. Start or continue a 7-Zip extraction.
2. Open Disk Space Monitor.
3. Click `Refresh 7-Zip`.
4. Select the detected 7-Zip process.
5. Click `Pause 7-Zip`.
6. Click `Resume 7-Zip` when ready to continue.

If the 7-Zip process was started as Administrator, this app may also need to be run as Administrator to pause or resume it.

## Requirements

### Running the EXE

- Windows 10 or Windows 11
- No Python installation required when using the standalone EXE

### Running from Source

- Windows 10 or Windows 11
- Python 3.x
- Tkinter, included with most standard Python for Windows installations
- No third-party Python packages are required for the app itself

## Run the App

### Option 1: Run the Standalone EXE

Open:

```text
dist/DiskSpaceMonitor_v1_3.exe
```

### Option 2: Run from Python Source

From this project folder:

```powershell
python disk_space_monitor_v1_3.py
```

## Build the Standalone EXE

The EXE is built with PyInstaller.

Install PyInstaller if needed:

```powershell
python -m pip install pyinstaller
```

Build:

```powershell
pyinstaller --onefile --windowed --name DiskSpaceMonitor_v1_3 disk_space_monitor_v1_3.py
```

The output will be created at:

```text
dist/DiskSpaceMonitor_v1_3.exe
```

## Project Structure

```text
DiskSpaceMonitor/
|-- README.md
|-- disk_space_monitor_v1_0.py
|-- disk_space_monitor_v1_1.py
|-- disk_space_monitor_v1_2.py
|-- disk_space_monitor_v1_3.py
|-- DiskSpaceMonitor_v1_0.spec
|-- DiskSpaceMonitor_v1_1.spec
|-- DiskSpaceMonitor_v1_2.spec
|-- DiskSpaceMonitor_v1_3.spec
|-- dist/
|   |-- DiskSpaceMonitor_v1_0.exe
|   |-- DiskSpaceMonitor_v1_1.exe
|   |-- DiskSpaceMonitor_v1_2.exe
|   `-- DiskSpaceMonitor_v1_3.exe
`-- build/
```

## Version History

### v1.3

- Added 7-Zip process detection for currently running extract/compress jobs.
- Added `Pause 7-Zip` and `Resume 7-Zip` buttons.
- Added a 7-Zip process dropdown and refresh button.
- Kept previous disk monitoring behavior and version comments.

### v1.2

- Added an always-on display refresh timer.
- Added threshold `YES` / `NO` information to the normal status view.
- Increased the window size so controls remain visible.
- Split display refresh from popup monitoring.

### v1.1

- Reworked the automatic monitoring loop.
- Added a dedicated topmost popup window for foreground alerts.
- Added last-check and next-check status text.
- Reset alert trigger when settings change or disk space recovers.

### v1.0

- Added the initial Tkinter GUI.
- Added drive selection.
- Added percent and GB threshold modes.
- Added foreground popup alerts.
- Added start/stop monitoring controls.
- Added live disk-space status updates.

## Notes

- The app monitors free space on the selected drive only.
- Popup alerts are enabled by clicking `Start Monitoring`.
- The status display refreshes automatically even when popup monitoring is off.
- Pausing a 7-Zip process suspends the process; it does not cancel or terminate the extraction.
- Resume the paused 7-Zip process before closing the app if you still need that extraction to continue.
- Running the app as Administrator may be required to pause or resume elevated 7-Zip processes.

## Troubleshooting

### The popup does not appear

Check that:

- `Threshold reached` says `YES`.
- `Popup monitoring` says `ON`.
- You clicked `Start Monitoring`.
- The selected disk is the disk you intended to monitor.

### The threshold says `NO` when expected to alert

For percent mode, the alert triggers when:

```text
current free percent <= threshold percent
```

For GB mode, the alert triggers when:

```text
current free GB <= threshold GB
```

### 7-Zip does not appear in the process list

Check that:

- A 7-Zip extraction is currently running.
- You clicked `Refresh 7-Zip`.
- The process is one of the supported names: `7z.exe`, `7za.exe`, `7zr.exe`, or `7zG.exe`.

### Pause or resume fails

Try running Disk Space Monitor as Administrator. Windows may block process control if the target 7-Zip process has higher privileges than this app.

## License

No license has been specified yet. Add a license file before publishing if you want others to reuse or modify the project under clear terms.

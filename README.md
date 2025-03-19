# eyesight
Python script that creates a full screen overlay to remind you to take breaks to mitigate eye-strain. Supports multiple monitors.

## Features

- Follows the 20-20-20 rule (take 20-second breaks every 20 minutes)
- Configurable break intervals and durations
- Works with multiple monitors
- System tray icon for easy access
- Settings can be changed during runtime via the tray menu

## Usage

Run the script directly:

```
python -m eyesight_reminder.main
```

With custom intervals and durations:

```
python -m eyesight_reminder.main --interval 1800 --duration 30
```

## Configuration

You can adjust the settings at any time by right-clicking the tray icon and selecting "Settings". This opens a dialog where you can change:

- Break interval: How often breaks occur (in seconds)
- Break duration: How long each break lasts (in seconds)

Changes take effect immediately.

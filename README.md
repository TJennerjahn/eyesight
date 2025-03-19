# eyesight-reminder

A simple utility that creates a full screen overlay to remind you to take breaks to mitigate eye-strain. Supports multiple monitors.

## Features

- Follows the 20-20-20 rule (take 20-second breaks every 20 minutes)
- Configurable break intervals and durations
- Works with multiple monitors
- System tray icon for easy access
- Settings can be changed during runtime via the tray menu

## Installation

### From PyPI

```bash
pip install eyesight-reminder
```

### From Source

Clone the repository and install:

```bash
git clone https://github.com/tjennerjahn/eyesight-reminder.git
cd eyesight-reminder
pip install .
```

## Usage

After installation, you can run the application with:

```bash
eyesight-reminder
```

Or run the module directly:

```bash
python -m eyesight_reminder.main
```

With custom intervals and durations:

```bash
eyesight-reminder --interval 1800 --duration 30
```

Or:

```bash
python -m eyesight_reminder.main --interval 1800 --duration 30
```

## Configuration

You can adjust the settings at any time by right-clicking the tray icon and selecting "Settings". This opens a dialog where you can change:

- Break interval: How often breaks occur (in seconds)
- Break duration: How long each break lasts (in seconds)

Changes take effect immediately.

## Development

### Requirements

- Python 3.8+
- PyQt5

### Setting up a development environment

```bash
# Clone the repository
git clone https://github.com/tjennerjahn/eyesight-reminder.git
cd eyesight-reminder

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

import argparse
import os
import pathlib
import signal
import socket
import sys
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)
from PyQt5.QtCore import Qt, QTimer, QSharedMemory, QSocketNotifier
from PyQt5.QtGui import QFont, QIcon
import tempfile

signal_receiver, signal_emitter = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
signal_receiver.setblocking(False)

shared_memory = None

# Create a NamedTemporaryFile that's deleted when closed
temp_file = tempfile.NamedTemporaryFile(prefix="eyesight_status_", delete=False)
file_path = temp_file.name
temp_file.close()


def cleanup():
    if shared_memory and shared_memory.isAttached():
        shared_memory.detach()
    try:
        os.remove(file_path)
    except OSError:
        pass


def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

def qt_signal_handler(sig, frame):
    # Send a message through the socket pair to notify the Qt app
    signal_emitter.send(b'x')
    # Also attempt direct exit in case the socket approach fails
    cleanup()
    # Don't call sys.exit here as it may interfere with the Qt event loop

shared_memory_key = "EyeSightApp_iIhtA63o6furmI"


class BreakReminderApp(QApplication):
    def __init__(self, break_interval, break_duration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_memory = QSharedMemory(shared_memory_key)
        self.break_interval = break_interval
        self.break_duration = break_duration
        self.time_left = break_interval
        self.paused = False
        self.overlays = []
        self.setup_tray_icon()

        # Set up the timer for the initial break interval
        self.initial_timer = QTimer(self)
        self.initial_timer.setInterval(1000)  # Update every second
        self.initial_timer.timeout.connect(self.update_time_left)
        self.initial_timer.start()
        
        # Set up signal handling through the socket
        self.signal_notifier = QSocketNotifier(signal_receiver.fileno(), QSocketNotifier.Read, self)
        self.signal_notifier.activated.connect(self.handle_signal)
        
        # Process events frequently to ensure signals are processed
        self.processEvents()
    
    # Override the event method to handle the KeyboardInterrupt exception (Ctrl+C)
    def event(self, event):
        # Process all other events normally
        return_value = super().event(event)
        # Check if Ctrl+C was pressed in the terminal
        if hasattr(signal, 'SIGINT'):
            try:
                # Check for Ctrl+C signal and exit if detected
                # This is a backup mechanism for handling Ctrl+C
                if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
                    # The default handler is installed, means Ctrl+C may not be handled
                    # Force Ctrl+C to be handled by our qt_signal_handler
                    signal.signal(signal.SIGINT, qt_signal_handler)
            except KeyboardInterrupt:
                # Exit if a keyboard interrupt is detected
                self.handle_signal()
                return True
        return return_value

    def handle_signal(self):
        # Clear the socket data
        signal_receiver.recv(1024)  # Receive more data to clear any backlog
        print("Shutdown signal received, exiting...")  # Add this to confirm signal receipt
        # Clean up and exit immediately without further event processing
        cleanup()
        # Exit both the application and the Python process
        QApplication.exit(0)  # Exit the Qt event loop
        sys.exit(0)  # Exit the Python process directly

    def setup_overlays(self):
        for screen in self.screens():
            overlay = self.setup_overlay_for_screen(screen)
            self.overlays.append(overlay)

    def setup_overlay_for_screen(self, screen):
        window = QMainWindow()
        window.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        window.setStyleSheet("background-color: black;")

        message = QLabel(window)
        message.setFont(QFont("Arial", 24, QFont.Bold))
        message.setStyleSheet("color: white;")
        message.setAlignment(Qt.AlignCenter)

        geometry = screen.geometry()
        window.setGeometry(geometry)
        message.setGeometry(0, 0, geometry.width(), geometry.height())

        window.showFullScreen()
        window.message_label = message  # Save reference to the message label
        return window

    def start_break(self):
        self.setup_overlays()
        self.time_left = self.break_duration
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Update every second
        self.timer.timeout.connect(self.update_overlays)
        self.timer.start()

        # Set up the timer to automatically quit the app after the break duration
        QTimer.singleShot(
            self.break_duration * 1000, self.end_break
        )  # Convert seconds to milliseconds

    def end_break(self):
        for overlay in self.overlays:
            overlay.close()
        self.overlays = []
        self.time_left = self.break_interval
        self.timer.stop()
        self.initial_timer.start()

    def update_time_left(self):
        if not self.paused:
            if self.time_left > 0:
                self.time_left -= 1
            else:
                if hasattr(self, "timer") and self.timer.isActive():
                    self.timer.stop()
                self.initial_timer.stop()
                self.start_break()
        self.update_tray_icon()
        self.write_time_to_file()

    def update_overlays(self):
        if not self.paused:
            if self.time_left > 0:
                for overlay in self.overlays:
                    overlay.message_label.setText(
                        f"Take a short pause!\nTime left: {self.time_left} seconds"
                    )
                self.time_left -= 1
            else:
                self.timer.stop()
        self.write_time_to_file()

    def setup_tray_icon(self):
        # Get the directory where the script is located
        script_dir = pathlib.Path(__file__).parent.absolute()
        icon_path = script_dir / "resources" / "icon.png"

        if not os.path.exists(icon_path):
            print(f"Warning: Icon file not found at {icon_path}")
        
        self.tray_icon = QSystemTrayIcon(
            QIcon(str(icon_path)), self
        )
        self.tray_menu = QMenu()

        self.show_remaining_action = QAction(
            f"Time until next break: {self.time_left} seconds", self
        )
        self.tray_menu.addAction(self.show_remaining_action)

        pause_action = QAction("Pause", self)
        pause_action.triggered.connect(self.toggle_pause)
        self.tray_menu.addAction(pause_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.update_tray_icon()

    def update_tray_icon(self):
        self.show_remaining_action.setText(
            f"Time until next break: {self.time_left} seconds"
        )
        self.tray_icon.setToolTip(f"Time until next break: {self.time_left} seconds")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_remaining_action.setText("Paused")
            self.tray_icon.setToolTip("Paused")
            if hasattr(self, "timer"):
                self.timer.stop()
        else:
            self.show_remaining_action.setText(
                f"Time until next break: {self.time_left} seconds"
            )
            self.tray_icon.setToolTip(
                f"Time until next break: {self.time_left} seconds"
            )
            if hasattr(self, "timer"):
                self.timer.start()

    def write_time_to_file(self):
        with open(file_path, "w") as f:
            if self.paused:
                f.write("-1")
            else:
                f.write(f"{self.time_left}")

    def quit(self):
        cleanup()
        super().quit()


def main(break_interval=1200, break_duration=20):
    global shared_memory

    # To make Ctrl+C work with PyQt, we need to follow these steps:
    # 1. Set the high DPI attribute before creating the app
    # 2. Create our custom app class that handles signals
    # 3. Set up signal handling after app creation
    # 4. Use our signal redirection system

    # Enable high DPI scaling before creating the application
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    # Create our custom application with signal handling
    break_reminder_app = BreakReminderApp(break_interval, break_duration, sys.argv)
    
    # Set up signal handling for Qt applications AFTER the application is created
    signal.signal(signal.SIGINT, qt_signal_handler)
    signal.signal(signal.SIGTERM, qt_signal_handler)

    # Single instance check using QSharedMemory
    shared_memory = QSharedMemory(shared_memory_key)
    if shared_memory.attach():
        QMessageBox.critical(
            None, "Error", "An instance of this application is already running."
        )
        sys.exit(1)
    if not shared_memory.create(1):
        QMessageBox.critical(None, "Error", "Unable to create shared memory segment.")
        sys.exit(1)

    # Start the application and ensure proper exit
    try:
        return_code = break_reminder_app.exec_()
        cleanup()
        sys.exit(return_code)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting...")
        cleanup()
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Display a full-screen pause reminder on all monitors."
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=1200, 
        help="Time between breaks in seconds (default: 1200, 20 minutes as per 20-20-20 rule)."
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=20,
        help="Duration of the break in seconds (default: 20, as per 20-20-20 rule)."
    )
    args = parser.parse_args()

    main(args.interval, args.duration)

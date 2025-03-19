import argparse
import os
import pathlib
import signal
import socket
import sys
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
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


class SettingsWindow(QMainWindow):
    def __init__(self, app, break_interval=1200, break_duration=20):
        super().__init__()
        self.app = app  # Store the app reference
        self.setWindowTitle("Eyesight Reminder Settings")
        self.setMinimumWidth(350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Make sure dialog doesn't close the app
        self.setAttribute(Qt.WA_QuitOnClose, False)
        
        # Store initial values
        self.initial_break_interval = break_interval
        self.initial_break_duration = break_duration
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add info label about 20-20-20 rule
        info_label = QLabel(
            "The 20-20-20 rule recommends looking at something\n"
            "20 feet away for 20 seconds every 20 minutes to\n"
            "reduce eye strain."
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Add description about current default settings
        current_settings_label = QLabel(
            f"Current settings: Break every {break_interval//60} minutes for {break_duration} seconds"
        )
        current_settings_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(current_settings_label)
        
        # Add a small spacer
        layout.addSpacing(10)
        
        form_layout = QFormLayout()
        
        # Interval setting - simplified layout
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(60)  # Minimum 1 minute
        self.interval_spinbox.setMaximum(7200)  # Maximum 2 hours
        self.interval_spinbox.setValue(break_interval)
        self.interval_spinbox.setSuffix(" seconds")
        
        # Show the interval in minutes for reference
        self.interval_minutes_label = QLabel(f"({break_interval // 60} minutes)")
        
        form_layout.addRow("Break interval:", self.interval_spinbox)
        form_layout.addRow("", self.interval_minutes_label)
        self.interval_spinbox.valueChanged.connect(self.update_minutes_label)
        
        # Duration setting - simplified layout
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setMinimum(5)  # Minimum 5 seconds
        self.duration_spinbox.setMaximum(300)  # Maximum 5 minutes
        self.duration_spinbox.setValue(break_duration)
        self.duration_spinbox.setSuffix(" seconds")
        form_layout.addRow("Break duration:", self.duration_spinbox)
        
        layout.addLayout(form_layout)
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def update_minutes_label(self, value):
        minutes = value // 60
        self.interval_minutes_label.setText(f"({minutes} minute{'s' if minutes != 1 else ''})")
    
    def get_settings(self):
        return {
            'break_interval': self.interval_spinbox.value(),
            'break_duration': self.duration_spinbox.value()
        }
        
    def settings_changed(self):
        """Check if settings have been changed from their initial values"""
        return (self.interval_spinbox.value() != self.initial_break_interval or
                self.duration_spinbox.value() != self.initial_break_duration)
    
    def save_settings(self):
        """Save settings to the app if they've changed"""
        if self.settings_changed():
            new_settings = self.get_settings()
            self.app.update_settings(new_settings)
        self.close()
        
    def closeEvent(self, event):
        """Override close event to handle window closing"""
        super().closeEvent(event)


class BreakReminderApp(QApplication):
    def __init__(self, break_interval, break_duration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_memory = QSharedMemory(shared_memory_key)
        self.break_interval = break_interval
        self.break_duration = break_duration
        self.time_left = break_interval
        self.paused = False
        self.overlays = []
        self.settings_window = None  # Will hold reference to settings window when open
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

        # Set up the timer to automatically end the break after the break duration
        self.break_end_timer = QTimer(self)
        self.break_end_timer.setSingleShot(True)
        self.break_end_timer.setInterval(self.break_duration * 1000)  # Convert seconds to milliseconds
        self.break_end_timer.timeout.connect(self.end_break)
        self.break_end_timer.start()

    def end_break(self):
        for overlay in self.overlays:
            overlay.close()
        self.overlays = []
        self.time_left = self.break_interval
        
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        
        if hasattr(self, "break_end_timer") and self.break_end_timer.isActive():
            self.break_end_timer.stop()
        
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
                time_text = self.format_time_remaining(self.time_left)
                for overlay in self.overlays:
                    overlay.message_label.setText(
                        f"Take a short pause!\nTime left: {time_text}"
                    )
                self.time_left -= 1
            else:
                self.timer.stop()
        self.write_time_to_file()

    def open_settings(self):
        """Open the settings window if it's not already open"""
        try:
            # If the window already exists and is visible, just bring it to front
            if self.settings_window and self.settings_window.isVisible():
                self.settings_window.activateWindow()
                self.settings_window.raise_()
                return
                
            # Otherwise create a new settings window
            self.settings_window = SettingsWindow(
                app=self,
                break_interval=self.break_interval,
                break_duration=self.break_duration
            )
            
            # Show the window and position it
            self.settings_window.show()
            
            # Position the window after it's shown to get correct size
            screen = self.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                window_width = self.settings_window.frameGeometry().width()
                window_height = self.settings_window.frameGeometry().height()
                self.settings_window.move(
                    screen_geometry.width() - window_width - 50,
                    screen_geometry.height() - window_height - 50
                )
            
        except Exception as e:
            # Print any errors for debugging
            print(f"Error opening settings window: {e}")
            
    def update_settings(self, new_settings):
        """Update app settings based on values from the settings window"""
        try:
            self.break_interval = new_settings['break_interval']
            self.break_duration = new_settings['break_duration']
            
            # If we're in the middle of counting down to a break
            if hasattr(self, "initial_timer") and self.initial_timer.isActive():
                self.time_left = self.break_interval
                self.update_tray_icon()
            
            # If we're in the middle of a break, update the duration
            elif self.overlays and hasattr(self, "timer") and self.timer.isActive():
                # If new duration is shorter than current remaining time, adjust time_left
                if self.break_duration < self.time_left:
                    self.time_left = self.break_duration
                    
                # Update the overlay text
                time_text = self.format_time_remaining(self.time_left)
                for overlay in self.overlays:
                    overlay.message_label.setText(
                        f"Take a short pause!\nTime left: {time_text}"
                    )
                    
                # Reset the timer that ends the break
                if hasattr(self, "break_end_timer") and self.break_end_timer.isActive():
                    self.break_end_timer.stop()
                
                # Restart the break end timer with the updated duration
                self.break_end_timer.setInterval(self.time_left * 1000)
                self.break_end_timer.start()
                
            print(f"Settings updated: interval={self.break_interval}s, duration={self.break_duration}s")
                
        except Exception as e:
            # Print any errors for debugging
            print(f"Error updating settings: {e}")
    
    def setup_tray_icon(self):
        # Get the directory where the script is located
        script_dir = pathlib.Path(__file__).parent.absolute()
        icon_path = script_dir / "resources" / "icon.png"

        # Fallback paths for different deployment scenarios
        fallback_paths = [
            # Current directory
            pathlib.Path.cwd() / "resources" / "icon.png",
            # AppImage or other bundled deployment
            pathlib.Path(sys.executable).parent / "resources" / "icon.png",
        ]

        # Try the primary path first
        if os.path.exists(icon_path):
            icon_file = str(icon_path)
        else:
            # Try fallback paths
            for path in fallback_paths:
                if os.path.exists(path):
                    icon_file = str(path)
                    break
            else:
                # If no paths work, use a warning message and continue
                print(f"Warning: Icon file not found at {icon_path} or fallbacks")
                icon_file = str(icon_path)  # Use the original path anyway
        
        self.tray_icon = QSystemTrayIcon(
            QIcon(icon_file), self
        )
        self.tray_menu = QMenu()

        time_text = self.format_time_remaining(self.time_left)
        self.show_remaining_action = QAction(
            f"Time until next break: {time_text}", self
        )
        self.tray_menu.addAction(self.show_remaining_action)

        pause_action = QAction("Pause", self)
        pause_action.triggered.connect(self.toggle_pause)
        self.tray_menu.addAction(pause_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.tray_menu.addAction(settings_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.update_tray_icon()

    def format_time_remaining(self, seconds):
        """Format seconds into a human-readable string (minutes or seconds)"""
        if seconds >= 60:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
            
    def update_tray_icon(self):
        time_text = self.format_time_remaining(self.time_left)
        self.show_remaining_action.setText(
            f"Time until next break: {time_text}"
        )
        self.tray_icon.setToolTip(f"Time until next break: {time_text}")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_remaining_action.setText("Paused")
            self.tray_icon.setToolTip("Paused")
            if hasattr(self, "timer"):
                self.timer.stop()
        else:
            time_text = self.format_time_remaining(self.time_left)
            self.show_remaining_action.setText(
                f"Time until next break: {time_text}"
            )
            self.tray_icon.setToolTip(
                f"Time until next break: {time_text}"
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
        """Properly clean up and quit the application"""
        # Close settings window if open
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.close()
            self.settings_window = None
            
        # Close any open overlays
        for overlay in self.overlays:
            overlay.close()
        self.overlays = []
        
        # Stop all timers
        if hasattr(self, "initial_timer") and self.initial_timer.isActive():
            self.initial_timer.stop()
            
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
            
        if hasattr(self, "break_end_timer") and self.break_end_timer.isActive():
            self.break_end_timer.stop()
        
        # Global cleanup
        cleanup()
        
        # Finally, quit the application
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

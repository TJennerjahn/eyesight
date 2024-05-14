import sys
import argparse
import signal
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QSharedMemory
from PyQt5.QtGui import QFont, QIcon

shared_memory = None

def cleanup():
    if shared_memory and shared_memory.isAttached():
        shared_memory.detach()

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

class BreakReminderApp(QApplication):
    def __init__(self, break_interval, break_duration, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def setup_overlays(self):
        for screen in self.screens():
            overlay = self.setup_overlay_for_screen(screen)
            self.overlays.append(overlay)

    def setup_overlay_for_screen(self, screen):
        window = QMainWindow()
        window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        window.setStyleSheet("background-color: black;")
        
        message = QLabel(window)
        message.setFont(QFont('Arial', 24, QFont.Bold))
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
        QTimer.singleShot(self.break_duration * 1000, self.end_break)  # Convert seconds to milliseconds

    def end_break(self):
        for overlay in self.overlays:
            overlay.close()
        self.overlays = []
        self.time_left = self.break_interval
        self.initial_timer.start()

    def update_time_left(self):
        if not self.paused:
            if self.time_left > 0:
                self.time_left -= 1
            else:
                self.initial_timer.stop()
                self.start_break()
        self.update_tray_icon()

    def update_overlays(self):
        if not self.paused:
            if self.time_left > 0:
                for overlay in self.overlays:
                    overlay.message_label.setText(f"Take a short pause!\nTime left: {self.time_left} seconds")
                self.time_left -= 1
            else:
                self.timer.stop()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self)
        self.tray_menu = QMenu()

        self.show_remaining_action = QAction(f"Time until next break: {self.time_left} seconds", self)
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
        self.show_remaining_action.setText(f"Time until next break: {self.time_left} seconds")
        self.tray_icon.setToolTip(f"Time until next break: {self.time_left} seconds")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_remaining_action.setText("Paused")
            self.tray_icon.setToolTip("Paused")
            if hasattr(self, 'timer'):
                self.timer.stop()
        else:
            self.show_remaining_action.setText(f"Time until next break: {self.time_left} seconds")
            self.tray_icon.setToolTip(f"Time until next break: {self.time_left} seconds")
            if hasattr(self, 'timer'):
                self.timer.start()

def main(break_interval, break_duration):
    global shared_memory

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = QApplication(sys.argv)

    # Single instance check using QSharedMemory
    shared_memory = QSharedMemory("BreakReminderApp")
    if shared_memory.attach():
        QMessageBox.critical(None, "Error", "An instance of this application is already running.")
        sys.exit(1)
    if not shared_memory.create(1):
        QMessageBox.critical(None, "Error", "Unable to create shared memory segment.")
        sys.exit(1)

    break_reminder_app = BreakReminderApp(break_interval, break_duration, sys.argv)
    sys.exit(break_reminder_app.exec_())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display a full-screen pause reminder on all monitors.")
    parser.add_argument('break_interval', type=int, help="Time between breaks in seconds.")
    parser.add_argument('break_duration', type=int, help="Duration of the break in seconds.")
    args = parser.parse_args()

    main(args.break_interval, args.break_duration)

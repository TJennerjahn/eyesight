import sys
import argparse
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

def setup_overlay_for_screen(screen, app, duration):
    # Create a window for each screen
    window = QMainWindow()
    window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    window.setAttribute(Qt.WA_TranslucentBackground)
    
    # Set black background
    window.setStyleSheet("background-color: black;")
    
    # Display the message
    message = QLabel("Take a short pause!", window)
    message.setFont(QFont('Arial', 24, QFont.Bold))
    message.setStyleSheet("color: white;")
    message.setAlignment(Qt.AlignCenter)
    
    # Use the screen's geometry to position the window and the message
    geometry = screen.geometry()
    message.setGeometry(geometry.width() // 2 - 150, geometry.height() // 2 - 50, 300, 100)
    window.setGeometry(geometry)

    window.showFullScreen()
    return window

def main(duration):
    app = QApplication(sys.argv)
    
    # Create overlays for all connected screens
    overlays = []
    for screen in app.screens():
        overlay = setup_overlay_for_screen(screen, app, duration)
        overlays.append(overlay)

    # Set a timer to automatically close the application after the specified duration
    QTimer.singleShot(duration * 1000, app.quit)  # Convert seconds to milliseconds
    sys.exit(app.exec_())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display a full-screen pause reminder on all monitors.")
    parser.add_argument('duration', type=int, help="Duration of the pause in seconds.")
    args = parser.parse_args()

    main(args.duration)

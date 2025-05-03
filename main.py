import sys
from PySide6.QtWidgets import QApplication
# Import your main window class (adjust path as needed)
from src.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # May need to set app name/version for settings later
    # app.setApplicationName("GPUMonQT")

    window = MainWindow() # Create an instance of your main window
    window.show()         # Show the window

    sys.exit(app.exec()) # Start the Qt event loop

# main.py (in project root)

import sys
from PySide6.QtWidgets import QApplication

# --- Import the MainWindow from the src package ---
# This works because main.py is in the parent directory of src,
# and src contains __init__.py making it a package.
try:
    from src.main_window import MainWindow
except ImportError as e:
    print(f"Error importing MainWindow from src package: {e}")
    print("Ensure src directory exists, contains __init__.py, main_window.py, and core.py.")
    sys.exit(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow() # Create an instance of the main window
    window.show()         # Show the window
    sys.exit(app.exec())  # Start the Qt event loop

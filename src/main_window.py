from PySide6.QtWidgets import QMainWindow, QLabel # Import necessary widgets
# If using Qt Designer and pyside6-uic:   
from PySide6.QtCore import QTimer, Slot, Qt, QFile # Add Qt here
from PySide6.QtUiTools import QUiLoader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GPU Monitor QT")
        # self.setGeometry(100, 100, 400, 200) # Optional: Set initial size/pos

        # --- Option 1: Create widgets directly in code (simple start) ---
        central_widget = QLabel("Hello GPU World!", self)
        central_widget.setAlignment(Qt.AlignmentFlag.AlignCenter) # Need: from PySide6.QtCore import Qt
        self.setCentralWidget(central_widget)

        # --- Option 2: Load from .ui file (if using Qt Designer) ---
        # self.load_ui()

        # Connect signals/slots later
        # self.setup_connections()

    # --- Example function for loading .ui file (if you use Designer) ---
    # def load_ui(self):
    #     loader = QUiLoader()
    #     path = "src/gpu_mon_qt/gui/ui_main_window.ui" # Adjust path
    #     ui_file = QFile(path)
    #     if not ui_file.open(QFile.ReadOnly):
    #         print(f"Cannot open {path}: {ui_file.errorString()}")
    #         sys.exit(-1)
    #     self.ui = loader.load(ui_file, self) # Load UI onto the QMainWindow
    #     ui_file.close()
    #     if not self.ui:
    #         print(loader.errorString())
    #         sys.exit(-1)
        # Access widgets via self.ui.widgetName (e.g., self.ui.myButton)

    # --- Example for setting up connections ---
    # def setup_connections(self):
    #     # Example: self.ui.myButton.clicked.connect(self.on_my_button_click)
    #     pass

    # --- Example slot function ---
    # def on_my_button_click(self):
    #     print("Button clicked!")
    #     # Update a label, call a core function, etc.

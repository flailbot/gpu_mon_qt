# src/main_window.py

import sys
from PySide6.QtWidgets import ( QMainWindow, QLabel, QApplication, QWidget,
                              QVBoxLayout, QGridLayout, QGroupBox, QPushButton ) # Added QPushButton
from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtGui import QFont

# Import core module using RELATIVE import
try:
    from . import core
    from .oc_window import OCWindow # Import the new OCWindow class
except ImportError as e:
     print(f"CRITICAL Error importing module: {e}")
     print("Ensure core.py and oc_window.py exist in the 'src' directory.")
     sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPU Monitor QT")
        # self.resize(450, 500) # Optional: Adjust size for more content including button

        # --- Instance variable to hold the OC window ---
        self.oc_window_instance = None

        # --- Main Layout Setup ---
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # Vertical layout

        # --- Static GPU Info Section (remains the same) ---
        self.static_info_group = QGroupBox("GPU Hardware Information")
        main_layout.addWidget(self.static_info_group)
        static_info_layout = QGridLayout(self.static_info_group)
        # (Static labels setup as before)
        self.gpu_name_label = QLabel("GPU Name:")
        self.gpu_name_value = QLabel("Loading...")
        self.vram_label = QLabel("Total VRAM:")
        self.vram_value = QLabel("Loading...")
        self.driver_label = QLabel("Driver Version:")
        self.driver_value = QLabel("Loading...")
        self.pcie_label = QLabel("Max PCIe Gen:")
        self.pcie_value = QLabel("Loading...")
        value_font_static = QFont(); value_font_static.setBold(True)
        self.gpu_name_value.setFont(value_font_static)
        self.vram_value.setFont(value_font_static)
        self.driver_value.setFont(value_font_static)
        self.pcie_value.setFont(value_font_static)
        static_info_layout.addWidget(self.gpu_name_label, 0, 0); static_info_layout.addWidget(self.gpu_name_value, 0, 1)
        static_info_layout.addWidget(self.vram_label, 1, 0); static_info_layout.addWidget(self.vram_value, 1, 1)
        static_info_layout.addWidget(self.driver_label, 2, 0); static_info_layout.addWidget(self.driver_value, 2, 1)
        static_info_layout.addWidget(self.pcie_label, 3, 0); static_info_layout.addWidget(self.pcie_value, 3, 1)

        # --- Dynamic GPU Status Section (remains the same) ---
        self.dynamic_status_group = QGroupBox("GPU Device Status")
        main_layout.addWidget(self.dynamic_status_group)
        dynamic_status_layout = QGridLayout(self.dynamic_status_group)
        # (Dynamic labels setup as before, including VRAM temp)
        self.temp_label_title = QLabel("Temperature:")
        self.temp_value = QLabel("Loading...")
        self.gpu_util_label_title = QLabel("GPU Utilization:")
        self.gpu_util_value = QLabel("Loading...")
        self.mem_util_label_title = QLabel("Memory Utilization:")
        self.mem_util_value = QLabel("Loading...")
        self.mem_free_label_title = QLabel("Memory Free:")
        self.mem_free_value = QLabel("Loading...")
        self.mem_used_label_title = QLabel("Memory Used:")
        self.mem_used_value = QLabel("Loading...")
        self.power_label_title = QLabel("Power Draw:")
        self.power_value = QLabel("Loading...")
        self.core_clock_label_title = QLabel("Core Clock:")
        self.core_clock_value = QLabel("Loading...")
        self.mem_clock_label_title = QLabel("Memory Clock:")
        self.mem_clock_value = QLabel("Loading...")
        self.fan_speed_label_title = QLabel("Fan Speed:")
        self.fan_speed_value = QLabel("Loading...")
        self.vram_temp_label_title = QLabel("VRAM Temperature:")
        self.vram_temp_value = QLabel("Loading...")
        value_font_dynamic = QFont(); value_font_dynamic.setBold(True)
        # Apply font to all value labels
        for label_val in [self.temp_value, self.gpu_util_value, self.mem_util_value,
                          self.mem_free_value, self.mem_used_value, self.power_value,
                          self.core_clock_value, self.mem_clock_value, self.fan_speed_value,
                          self.vram_temp_value]:
            label_val.setFont(value_font_dynamic)
        row = 0
        dynamic_status_layout.addWidget(self.temp_label_title, row, 0); dynamic_status_layout.addWidget(self.temp_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.gpu_util_label_title, row, 0); dynamic_status_layout.addWidget(self.gpu_util_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_util_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_util_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_free_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_free_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_used_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_used_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.power_label_title, row, 0); dynamic_status_layout.addWidget(self.power_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.core_clock_label_title, row, 0); dynamic_status_layout.addWidget(self.core_clock_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_clock_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_clock_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.fan_speed_label_title, row, 0); dynamic_status_layout.addWidget(self.fan_speed_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.vram_temp_label_title, row, 0); dynamic_status_layout.addWidget(self.vram_temp_value, row, 1); row += 1


        # --- OC Settings Button ---
        self.oc_button = QPushButton("OC Settings")
        self.oc_button.clicked.connect(self.open_oc_settings_window)
        main_layout.addWidget(self.oc_button) # Add button at the bottom of the main layout


        # --- Load Initial Static Data & Start Timer ---
        self.load_static_gpu_info()
        self._vram_helper_checked = False # For VRAM temp helper
        self._vram_helper_available = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_dynamic_status)
        self.timer.start()
        self.update_dynamic_status() # Initial update

    def load_static_gpu_info(self):
        # ... (remains the same) ...
        print("Fetching static GPU info...")
        info = core.get_gpu_static_info()
        if info:
            self.gpu_name_value.setText(info.get("name", "N/A"))
            self.vram_value.setText(info.get("vram", "N/A"))
            self.driver_value.setText(info.get("driver", "N/A"))
            self.pcie_value.setText(info.get("pcie_max_gen", "N/A"))
            print("Static info loaded successfully.")
        else:
            error_text = "Error"
            self.gpu_name_value.setText(error_text)
            self.vram_value.setText(error_text)
            self.driver_value.setText(error_text)
            self.pcie_value.setText(error_text)
            print("Failed to load static GPU info. Is nvidia-smi working?")

    @Slot()
    def update_dynamic_status(self):
        # ... (remains mostly the same, including VRAM temp logic) ...
        status = core.get_gpu_dynamic_status()
        if status:
            def format_value(key, unit, default_val="?"):
                val = status.get(key, default_val)
                if val == "N/A": return "N/A"
                return f"{val} {unit}"
            self.temp_value.setText(format_value("temperature", "°C"))
            self.gpu_util_value.setText(format_value("gpu_util", "%"))
            self.mem_util_value.setText(format_value("mem_util", "%"))
            self.mem_free_value.setText(format_value("mem_free", "MiB"))
            self.mem_used_value.setText(format_value("mem_used", "MiB"))
            self.power_value.setText(format_value("power", "W"))
            self.core_clock_value.setText(format_value("core_clock", "MHz"))
            self.mem_clock_value.setText(format_value("mem_clock", "MHz"))
            self.fan_speed_value.setText(format_value("fan_speed", "%"))
        else:
            error_text = "N/A"
            self.temp_value.setText(error_text)
            self.gpu_util_value.setText(error_text)
            self.mem_util_value.setText(error_text)
            self.mem_free_value.setText(error_text)
            self.mem_used_value.setText(error_text)
            self.power_value.setText(error_text)
            self.core_clock_value.setText(error_text)
            self.mem_clock_value.setText(error_text)
            self.fan_speed_value.setText(error_text)

        vram_temp_status = "N/A"
        if not self._vram_helper_checked:
             if core.HELPER_PATH:
                 initial_vram_read = core.get_vram_temperature()
                 if isinstance(initial_vram_read, int):
                     self._vram_helper_available = True
                     vram_temp_status = f"{initial_vram_read} °C"
                 else:
                     self._vram_helper_available = False
                     vram_temp_status = initial_vram_read
                     if vram_temp_status in ["No Helper", "Not Supported", "Error"]:
                          self.vram_temp_label_title.setVisible(False)
                          self.vram_temp_value.setVisible(False)
                     elif vram_temp_status == "No Root?":
                          self.vram_temp_value.setToolTip("Requires passwordless sudo for helper.")
                          self.vram_temp_value.setText(vram_temp_status)
                     else:
                          self.vram_temp_value.setText(vram_temp_status)
             else:
                 self._vram_helper_available = False
                 vram_temp_status = "No Helper"
                 self.vram_temp_label_title.setVisible(False)
                 self.vram_temp_value.setVisible(False)
             self._vram_helper_checked = True
        elif self._vram_helper_available:
            vram_temp = core.get_vram_temperature()
            if isinstance(vram_temp, int):
                vram_temp_status = f"{vram_temp} °C"
            else:
                vram_temp_status = vram_temp
        if self.vram_temp_label_title.isVisible():
             self.vram_temp_value.setText(vram_temp_status)


    # --- Slot to open the OC Settings window ---
    @Slot()
    def open_oc_settings_window(self):
        """
        Opens the OC Settings window.
        If an instance already exists and is visible, it brings it to the front.
        If not, it creates a new instance.
        """
        
        if self.oc_window_instance is None:
            # Create a new instance if one doesn't exist (or was closed and deleted)
            desired_gpu_id = 0
            self.oc_window_instance = OCWindow(gpu_id=desired_gpu_id, parent=self)
            # Connect the destroyed signal to a slot that nullifies our reference
            # This is important so we know to recreate it if the user closes it and clicks again
            self.oc_window_instance.destroyed.connect(self._on_oc_window_destroyed)
            print(f"DEBUG: OCWindow instance created: {self.oc_window_instance}")
            self.oc_window_instance.show()
            print(f"DEBUG: OCWindow.show() called. IsVisible: {self.oc_window_instance.isVisible()}")
            print(f"DEBUG: OCWindow geometry after show: {self.oc_window_instance.geometry()}")
            print(f"DEBUG: OCWindow window flags: {self.oc_window_instance.windowFlags()}")
            # Force it to the front again, just in case
            self.oc_window_instance.raise_()
            self.oc_window_instance.activateWindow()
        else:
            # If an instance exists, just show it (in case it was hidden) and activate
            print(f"DEBUG: OCWindow instance already exists: {self.oc_window_instance}")
            self.oc_window_instance.show()
            print(f"DEBUG: Existing OCWindow.show() called. IsVisible: {self.oc_window_instance.isVisible()}")
            self.oc_window_instance.activateWindow() # Bring to front
            print(f"DEBUG: Existing OCWindow.activateWindow() called.")

    @Slot()
    def _on_oc_window_destroyed(self):
        """
        Slot connected to the destroyed signal of the OCWindow.
        Sets the instance reference to None so a new window can be created next time.
        """
        self.oc_window_instance = None

# No __main__ block needed here
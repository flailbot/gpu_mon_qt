# src/main_window.py

import sys
from PySide6.QtWidgets import ( QMainWindow, QLabel, QApplication, QWidget,
                              QVBoxLayout, QGridLayout, QGroupBox )
from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtGui import QFont

# Import core module using RELATIVE import
try:
    from . import core
except ImportError as e:
     print(f"CRITICAL Error importing core module using relative import: {e}")
     print("Ensure core.py exists in the 'src' directory alongside main_window.py.")
     sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPU Monitor QT")
        # self.resize(450, 450) # Optional: Adjust size for more content

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


        # --- Dynamic GPU Status Section ---
        self.dynamic_status_group = QGroupBox("GPU Device Status")
        main_layout.addWidget(self.dynamic_status_group)
        dynamic_status_layout = QGridLayout(self.dynamic_status_group)

        # Create labels for dynamic status (Titles and Values)
        self.temp_label_title = QLabel("Temperature:")
        self.temp_value = QLabel("Loading...")
        self.vram_temp_label_title = QLabel("VRAM Temperature:")
        self.vram_temp_value = QLabel("Loading...") # Experimental
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

        # Optional: Style dynamic value labels
        value_font_dynamic = QFont(); value_font_dynamic.setBold(True)
        self.temp_value.setFont(value_font_dynamic)
        self.vram_temp_value.setFont(value_font_dynamic)
        self.gpu_util_value.setFont(value_font_dynamic)
        self.mem_util_value.setFont(value_font_dynamic)
        self.mem_free_value.setFont(value_font_dynamic)
        self.mem_used_value.setFont(value_font_dynamic)
        self.power_value.setFont(value_font_dynamic) # Style new labels
        self.core_clock_value.setFont(value_font_dynamic)
        self.mem_clock_value.setFont(value_font_dynamic)
        self.fan_speed_value.setFont(value_font_dynamic)

        # Add dynamic status labels to the grid layout
        row = 0
        dynamic_status_layout.addWidget(self.temp_label_title, row, 0); dynamic_status_layout.addWidget(self.temp_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.vram_temp_label_title, row, 0); dynamic_status_layout.addWidget(self.vram_temp_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.gpu_util_label_title, row, 0); dynamic_status_layout.addWidget(self.gpu_util_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_util_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_util_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_free_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_free_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_used_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_used_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.power_label_title, row, 0); dynamic_status_layout.addWidget(self.power_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.core_clock_label_title, row, 0); dynamic_status_layout.addWidget(self.core_clock_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.mem_clock_label_title, row, 0); dynamic_status_layout.addWidget(self.mem_clock_value, row, 1); row += 1
        dynamic_status_layout.addWidget(self.fan_speed_label_title, row, 0); dynamic_status_layout.addWidget(self.fan_speed_value, row, 1); row += 1

        # --- Load Initial Static Data ---
        self.load_static_gpu_info()

        # --- Setup Dynamic Data Update Timer ---
        self.timer = QTimer(self)
        self.timer.setInterval(1000) # 1 second
        self.timer.timeout.connect(self.update_dynamic_status)
        self._vram_helper_checked = False
        self._vram_helper_available = False
        self.timer.start()

        # --- Initial Dynamic Data Update ---
        self.update_dynamic_status() # Get the first reading immediately

    def load_static_gpu_info(self):
        """Fetches static GPU info ONCE and updates the labels."""
        print("Fetching static GPU info...")
        info = core.get_gpu_static_info()
        if info:
            self.gpu_name_value.setText(info.get("name", "N/A"))
            self.vram_value.setText(info.get("vram", "N/A"))
            self.driver_value.setText(info.get("driver", "N/A"))
            self.pcie_value.setText(info.get("pcie_max_gen", "N/A"))
            print("Static info loaded successfully.")
        else:
            # Handle error case
            error_text = "Error"
            self.gpu_name_value.setText(error_text)
            self.vram_value.setText(error_text)
            self.driver_value.setText(error_text)
            self.pcie_value.setText(error_text)
            print("Failed to load static GPU info. Is nvidia-smi working?")

    @Slot()
    def update_dynamic_status(self):
        """Fetches ALL dynamic GPU status from core.py and updates the labels."""
        status = core.get_gpu_dynamic_status() # Call the updated function

        if status:
            # Helper function to format value with unit, handling N/A
            def format_value(key, unit, default_val="?"):
                val = status.get(key, default_val)
                if val == "N/A":
                    return "N/A" # Return N/A directly without unit if not applicable
                return f"{val} {unit}"

            # Update the labels in the dynamic status box using the helper
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
            # Handle error case where core function returned None
            error_text = "N/A" # Or "Error"
            self.temp_value.setText(error_text)
            self.gpu_util_value.setText(error_text)
            self.mem_util_value.setText(error_text)
            self.mem_free_value.setText(error_text)
            self.mem_used_value.setText(error_text)
            self.power_value.setText(error_text)
            self.core_clock_value.setText(error_text)
            self.mem_clock_value.setText(error_text)
            self.fan_speed_value.setText(error_text)

        # --- Fetch VRAM Temp using Helper (conditionally) ---
        vram_temp_status = "N/A" # Default status

        # Check helper availability only once for efficiency
        if not self._vram_helper_checked:
             # Check if helper path was found by core.py
             if core.HELPER_PATH:
                 # Attempt a first read to see if sudo works / device compatible
                 initial_vram_read = core.get_vram_temperature()
                 if isinstance(initial_vram_read, int):
                     self._vram_helper_available = True
                     vram_temp_status = f"{initial_vram_read} °C" # Use the first read
                 else:
                     self._vram_helper_available = False
                     vram_temp_status = initial_vram_read # Show error status (No Root?, No Helper, etc)
                     # Hide the label if helper is definitively unavailable or unsupported after first check
                     if vram_temp_status in ["No Helper", "Not Supported", "Error"]:
                          self.vram_temp_label_title.setVisible(False)
                          self.vram_temp_value.setVisible(False)
                     elif vram_temp_status == "No Root?":
                          self.vram_temp_value.setToolTip("Requires passwordless sudo for helper or running main app as root (not recommended).")
                          self.vram_temp_value.setText(vram_temp_status) # Show No Root?
                     else: # Other errors like Parse Err, Py Error, Timeout
                          self.vram_temp_value.setText(vram_temp_status)

             else: # Helper path wasn't found at startup
                 self._vram_helper_available = False
                 vram_temp_status = "No Helper"
                 self.vram_temp_label_title.setVisible(False)
                 self.vram_temp_value.setVisible(False)

             self._vram_helper_checked = True # Mark as checked

        elif self._vram_helper_available: # If available, get updates
            vram_temp = core.get_vram_temperature()
            if isinstance(vram_temp, int):
                vram_temp_status = f"{vram_temp} °C"
            else:
                vram_temp_status = vram_temp # Show error like N/A, Timeout, etc.
                # Maybe hide it if it persistently fails? Or just show error.
                if vram_temp_status == "No Root?":
                    # If sudo worked once then failed, something changed. Keep showing error.
                    pass

        # Update VRAM Temp label only if it wasn't hidden
        if self.vram_temp_label_title.isVisible():
             self.vram_temp_value.setText(vram_temp_status)


# ... (No __main__ block needed here) ...
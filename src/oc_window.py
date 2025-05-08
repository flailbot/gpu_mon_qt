# oc_window.py
import sys
from PySide6 import QtWidgets, QtCore, QtGui
try:
    from .overclocking import (
        get_gpu_overclock_info,
        apply_power_limit,
        apply_clock_offset
    )
except ImportError:
    # Fallback for running oc_window.py directly (if overclocking.py is in the same dir)
    # This might be less robust if your project structure gets more complex
    # but useful for isolated testing.
    if __name__ == "__main__":
        from overclocking import (
            get_gpu_overclock_info,
            apply_power_limit,
            apply_clock_offset
        )
    else:
        raise # Re-raise the import error if not running directly

# *** MODIFIED COOLBITS INSTRUCTIONS ***
COOLBITS_INSTRUCTIONS = """
<b>Overclocking Features Disabled</b><br><br>
Manual clock offsets and fan control require enabling 'Coolbits' in your system's Xorg configuration.<br><br>
<b>Steps:</b>
<ol>
<li>Open a terminal.</li>
<li>Edit your Nvidia Xorg config file with root privileges. Common locations:
    <ul>
    <li><code>sudo nano /etc/X11/xorg.conf</code> (if it exists)</li>
    <li><code>sudo nano /etc/X11/xorg.conf.d/20-nvidia.conf</code> (common on newer systems)</li>
    </ul>
    You may need to create the file/directory if it doesn't exist. Consult your distribution's documentation if unsure.
</li>
<li>Find the section related to your Nvidia GPU. This could be:
    <ul>
        <li><code>Section "Device"</code> (often contains <code>Driver "nvidia"</code>)</li>
        <li><b>OR</b> <code>Section "Screen"</code> (often associated with the Nvidia "Device" identifier)</li>
    </ul>
</li>
<li>Add or modify the following line <i>inside</i> the appropriate section:<br>
    <code>Option "Coolbits" "28"</code><br>
    (Value 28 enables fan control and clock offsets. Use 31 for all features.)</li>
<li>Save the file and exit the editor (e.g., Ctrl+O, Enter, Ctrl+X in nano).</li>
<li><b>Log out of your desktop session and log back in</b>, or restart your computer.</li>
</ol>
After restarting your session, refresh this tool.
"""

class OCWindow(QtWidgets.QWidget):
    def __init__(self, gpu_id=0, parent=None):
        super().__init__(parent)
        self.gpu_id = gpu_id
        self.setWindowTitle(f"Nvidia Overclocking (GPU {self.gpu_id})")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        self.current_oc_data = {}

        self.layout = QtWidgets.QVBoxLayout() # Create layout without parent first
        self.setLayout(self.layout)           # Then apply it to this widget
        
        # --- Crucial for proper cleanup when closed by the user ---
        # This attribute ensures that when the window is closed (e.g., clicking 'X'),
        # the Qt widget is deleted. This allows Python's garbage collector to reclaim memory
        # and triggers the 'destroyed' signal in MainWindow if connected.
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        # (Status Label, Coolbits Warning Area, Refresh Button - unchanged)
        self.status_label = QtWidgets.QLabel("Initializing..."); self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter); self.status_label.setWordWrap(True); self.layout.addWidget(self.status_label)
        self.coolbits_warning_widget = QtWidgets.QWidget(); self.coolbits_layout = QtWidgets.QHBoxLayout(self.coolbits_warning_widget); self.coolbits_icon = QtWidgets.QLabel(); self.coolbits_icon.setPixmap(QtGui.QIcon.fromTheme("dialog-warning", self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)).pixmap(32, 32)); self.coolbits_label = QtWidgets.QLabel("Coolbits not detected..."); self.coolbits_button = QtWidgets.QPushButton("Show Instructions"); self.coolbits_button.clicked.connect(self.show_coolbits_instructions); self.coolbits_layout.addWidget(self.coolbits_icon); self.coolbits_layout.addWidget(self.coolbits_label, 1); self.coolbits_layout.addWidget(self.coolbits_button); self.coolbits_warning_widget.setVisible(False); self.layout.addWidget(self.coolbits_warning_widget)
        self.refresh_button = QtWidgets.QPushButton("Refresh Values"); self.refresh_button.setIcon(QtGui.QIcon.fromTheme("view-refresh")); self.refresh_button.clicked.connect(self.populate_values); top_layout = QtWidgets.QHBoxLayout(); top_layout.addStretch(); top_layout.addWidget(self.refresh_button); self.layout.addLayout(top_layout)


        # --- Power Limit Section (MODIFIED: Added Default Label) ---
        self.power_group = QtWidgets.QGroupBox("Power Limit (W)")
        self.power_layout = QtWidgets.QFormLayout(self.power_group)
        self.lbl_power_current = QtWidgets.QLabel("N/A")
        self.lbl_power_min = QtWidgets.QLabel("N/A")
        self.lbl_power_max = QtWidgets.QLabel("N/A")
        # *** ADDED Default Power Label ***
        self.lbl_power_default = QtWidgets.QLabel("N/A")
        self.spin_power_limit = QtWidgets.QSpinBox(); self.spin_power_limit.setSuffix(" W"); self.spin_power_limit.setSingleStep(1)
        self.btn_apply_power = QtWidgets.QPushButton("Apply"); self.btn_apply_power.clicked.connect(self._apply_power_limit_clicked)
        self.power_layout.addRow("Current:", self.lbl_power_current)
        # *** ADDED Default Row ***
        self.power_layout.addRow("Default:", self.lbl_power_default)
        self.power_layout.addRow("Min:", self.lbl_power_min)
        self.power_layout.addRow("Max:", self.lbl_power_max)
        power_apply_layout = QtWidgets.QHBoxLayout(); power_apply_layout.addWidget(self.spin_power_limit, 1); power_apply_layout.addWidget(self.btn_apply_power)
        self.power_layout.addRow("Set Limit:", power_apply_layout)
        self.layout.addWidget(self.power_group)


        # --- Core Clock Offset Section (Unchanged) ---
        self.core_group = QtWidgets.QGroupBox("Core Clock Offset (MHz)")
        self.core_layout = QtWidgets.QFormLayout(self.core_group)
        self.lbl_core_offset_current = QtWidgets.QLabel("N/A"); self.lbl_core_offset_min = QtWidgets.QLabel("N/A"); self.lbl_core_offset_max = QtWidgets.QLabel("N/A")
        self.spin_core_offset = QtWidgets.QSpinBox(); self.spin_core_offset.setSuffix(" MHz"); self.spin_core_offset.setSingleStep(5)
        self.btn_apply_core = QtWidgets.QPushButton("Apply"); self.btn_apply_core.clicked.connect(self._apply_core_offset_clicked)
        self.core_layout.addRow("Current:", self.lbl_core_offset_current); self.core_layout.addRow("Min Limit:", self.lbl_core_offset_min); self.core_layout.addRow("Max Limit:", self.lbl_core_offset_max)
        core_apply_layout = QtWidgets.QHBoxLayout(); core_apply_layout.addWidget(self.spin_core_offset, 1); core_apply_layout.addWidget(self.btn_apply_core); self.core_layout.addRow("Set Offset:", core_apply_layout)
        self.layout.addWidget(self.core_group)

        # --- Memory Clock Offset Section (Unchanged) ---
        self.mem_group = QtWidgets.QGroupBox("Memory Clock Offset (MHz)")
        self.mem_layout = QtWidgets.QFormLayout(self.mem_group)
        self.lbl_mem_offset_current = QtWidgets.QLabel("N/A"); self.lbl_mem_offset_min = QtWidgets.QLabel("N/A"); self.lbl_mem_offset_max = QtWidgets.QLabel("N/A")
        self.spin_mem_offset = QtWidgets.QSpinBox(); self.spin_mem_offset.setSuffix(" MHz"); self.spin_mem_offset.setSingleStep(10)
        self.btn_apply_mem = QtWidgets.QPushButton("Apply"); self.btn_apply_mem.clicked.connect(self._apply_mem_offset_clicked)
        self.mem_layout.addRow("Current:", self.lbl_mem_offset_current); self.mem_layout.addRow("Min Limit:", self.lbl_mem_offset_min); self.mem_layout.addRow("Max Limit:", self.lbl_mem_offset_max)
        mem_apply_layout = QtWidgets.QHBoxLayout(); mem_apply_layout.addWidget(self.spin_mem_offset, 1); mem_apply_layout.addWidget(self.btn_apply_mem); self.mem_layout.addRow("Set Offset:", mem_apply_layout)
        self.layout.addWidget(self.mem_group)

        self.layout.addStretch()
        self.populate_values()

    # (format_value, show_coolbits_instructions, set_controls_enabled - unchanged)
    def format_value(self, value, unit="", precision=2, add_plus=False):
        # (Implementation from previous version)
        if value is None: return "N/A"
        try:
            f_value = float(value); prefix = "+" if add_plus and f_value > 0 else ""
            formatted = f"{prefix}{f_value:.{precision}f}"
            if precision > 0 and formatted.endswith('.' + '0' * precision): formatted = formatted[:- (precision + 1)]
            return f"{formatted} {unit}".strip()
        except (ValueError, TypeError): return str(value)
    def show_coolbits_instructions(self): QtWidgets.QMessageBox.information(self, "Enable Overclocking Features (Coolbits)", COOLBITS_INSTRUCTIONS)
    def set_controls_enabled(self, enabled, coolbits_ok=False):
        # (Implementation from previous version)
        self.refresh_button.setEnabled(enabled); power_data_ok = self.current_oc_data.get('power_limit_min') is not None; self.spin_power_limit.setEnabled(enabled and power_data_ok); self.btn_apply_power.setEnabled(enabled and power_data_ok); core_data_ok = self.current_oc_data.get('core_offset_min') is not None; mem_data_ok = self.current_oc_data.get('memory_offset_min') is not None; self.spin_core_offset.setEnabled(enabled and core_data_ok and coolbits_ok); self.btn_apply_core.setEnabled(enabled and core_data_ok and coolbits_ok); self.spin_mem_offset.setEnabled(enabled and mem_data_ok and coolbits_ok); self.btn_apply_mem.setEnabled(enabled and mem_data_ok and coolbits_ok)


    def populate_values(self):
        # (Fetch logic unchanged)
        self.status_label.setText(f"Fetching data for GPU {self.gpu_id}..."); self.set_controls_enabled(False); QtWidgets.QApplication.processEvents()
        self.current_oc_data = get_gpu_overclock_info(self.gpu_id)
        if self.current_oc_data is None or not self.current_oc_data: self.status_label.setText(f"<font color='red'>Error fetching data for GPU {self.gpu_id}.</font>"); self.coolbits_warning_widget.setVisible(False); self.set_controls_enabled(False); self.refresh_button.setEnabled(True); return

        coolbits_enabled = self.current_oc_data.get('coolbits_enabled', False); self.coolbits_warning_widget.setVisible(not coolbits_enabled)
        self.status_label.setText(f"Current settings (GPU {self.gpu_id}). Ready.")

        # Populate Power (MODIFIED: Added Default)
        p_curr = self.current_oc_data.get('power_limit_current'); p_min = self.current_oc_data.get('power_limit_min'); p_max = self.current_oc_data.get('power_limit_max'); p_def = self.current_oc_data.get('power_limit_default') # Get default
        self.lbl_power_current.setText(self.format_value(p_curr, "W"))
        self.lbl_power_default.setText(self.format_value(p_def, "W")) # Set default label
        self.lbl_power_min.setText(self.format_value(p_min, "W")); self.lbl_power_max.setText(self.format_value(p_max, "W"))
        if p_min is not None and p_max is not None: self.spin_power_limit.setRange(int(p_min), int(p_max)); self.spin_power_limit.setValue(int(p_curr or p_min))

        # Populate Core Clock Offset (Unchanged logic)
        c_curr = self.current_oc_data.get('core_offset_current'); c_min = self.current_oc_data.get('core_offset_min'); c_max = self.current_oc_data.get('core_offset_max')
        self.lbl_core_offset_current.setText(self.format_value(c_curr, "MHz", 0, True)); min_label = f"{self.format_value(c_min, 'MHz', 0, True)}"; max_label = f"{self.format_value(c_max, 'MHz', 0, True)}"
        # Note: Placeholders are added based on defaults in overclocking.py now
        self.lbl_core_offset_min.setText(min_label); self.lbl_core_offset_max.setText(max_label)
        if c_min is not None and c_max is not None: self.spin_core_offset.setRange(int(c_min), int(c_max)); self.spin_core_offset.setValue(int(c_curr or 0))

        # Populate Memory Clock Offset (Unchanged logic)
        m_curr = self.current_oc_data.get('memory_offset_current'); m_min = self.current_oc_data.get('memory_offset_min'); m_max = self.current_oc_data.get('memory_offset_max')
        self.lbl_mem_offset_current.setText(self.format_value(m_curr, "MHz", 0, True)); min_label = f"{self.format_value(m_min, 'MHz', 0, True)}"; max_label = f"{self.format_value(m_max, 'MHz', 0, True)}"
        self.lbl_mem_offset_min.setText(min_label); self.lbl_mem_offset_max.setText(max_label)
        if m_min is not None and m_max is not None: self.spin_mem_offset.setRange(int(m_min), int(m_max)); self.spin_mem_offset.setValue(int(m_curr or 0))

        self.set_controls_enabled(True, coolbits_ok=coolbits_enabled)


    # (_apply_power_limit_clicked, _apply_core_offset_clicked, _apply_mem_offset_clicked, _handle_apply_result - unchanged)
    def _apply_power_limit_clicked(self):
        desired_power = self.spin_power_limit.value(); self.status_label.setText(f"Applying power limit {desired_power}W..."); self.set_controls_enabled(False, coolbits_ok=self.current_oc_data.get('coolbits_enabled')); QtWidgets.QApplication.processEvents(); success, message = apply_power_limit(self.gpu_id, desired_power); self._handle_apply_result(success, message)
    def _apply_core_offset_clicked(self):
        desired_offset = self.spin_core_offset.value(); self.status_label.setText(f"Applying core offset {desired_offset:+}MHz..."); self.set_controls_enabled(False, coolbits_ok=True); QtWidgets.QApplication.processEvents(); success, message = apply_clock_offset(self.gpu_id, 'core', desired_offset); self._handle_apply_result(success, message)
    def _apply_mem_offset_clicked(self):
        desired_offset = self.spin_mem_offset.value(); self.status_label.setText(f"Applying memory offset {desired_offset:+}MHz..."); self.set_controls_enabled(False, coolbits_ok=True); QtWidgets.QApplication.processEvents(); success, message = apply_clock_offset(self.gpu_id, 'memory', desired_offset); self._handle_apply_result(success, message)
    def _handle_apply_result(self, success, message):
        if success: self.status_label.setText(f"<font color='green'>{message}</font>"); QtCore.QTimer.singleShot(500, self.populate_values)
        else: self.status_label.setText(f"<font color='red'>Error: {message}</font>"); self.set_controls_enabled(True, coolbits_ok=self.current_oc_data.get('coolbits_enabled')); QtWidgets.QMessageBox.critical(self, "Apply Failed", message)

# (Main execution block remains the same)
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv); gpu_id_to_test = 0; window = OCWindow(gpu_id=gpu_id_to_test); window.show(); sys.exit(app.exec())
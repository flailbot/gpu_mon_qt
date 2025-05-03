# GPU Monitor QT

A simple Nvidia GPU monitoring tool for **Linux**, built with Python and PySide6.

*(Work in progress - v0.1)*

## Features (Implemented - v0.1)

**GPU Hardware Info:**
*   Display GPU Name (e.g., NVIDIA GeForce RTX 4070)
*   Display Total VRAM (e.g., 8192 MiB)
*   Display Current Driver Version
*   Display Maximum PCIe Link Generation

**GPU Monitoring (Updates every second):**
*   Display GPU Core Temperature (°C)
*   Display GPU Utilization (%)
*   Display Memory Controller Utilization (%)
*   Display Free Video Memory (MiB)
*   Display Used Video Memory (MiB)
*   Display Current Power Draw (W)
*   Display Current Graphics (Core) Clock (MHz)
*   Display Current Memory Clock (MHz)
*   Display Current GPU Fan Speed (%)

## Features (Planned)

*   Display GPU Hot Spot / Junction / Memory Temperature (if available via `nvidia-smi` query)
*   Add graphs/plots for monitored values over time
*   Control Fan Speed / Fan Curve (requires elevated privileges)
*   Control Clock Offsets (requires elevated privileges)
*   Control Power Limit (requires elevated privileges)
*   Create Profiles for settings

## Installation

**Prerequisites:**

*   **Linux Operating System:** This tool is currently designed **only for Linux**.
*   **NVIDIA GPU:** An NVIDIA graphics card is required.
*   **NVIDIA Proprietary Drivers:** You must have the official NVIDIA drivers installed. These drivers provide the `nvidia-smi` command-line utility, which this tool relies on. You can usually install these through your distribution's package manager or download them from the NVIDIA website.
*   **`nvidia-smi` command:** Verify this command works in your terminal by running `nvidia-smi`. If it doesn't, your drivers are likely not installed correctly or not loaded.
*   **Python:** Python 3 (version 3.7 or newer recommended) needs to be installed. Check with `python3 --version`.
*   **Git:** Required to clone the repository.

**Steps:**

1.  **Clone the repository:**
    Open your terminal and run:
    ```bash
    git clone https://github.com/flailbot/gpu_mon_qt.git
    ```

2.  **Navigate into the project directory:**
    ```bash
    cd gpu_mon_qt
    ```

3.  **(Recommended) Create and activate a Python virtual environment:**
    This isolates the project's dependencies.
    ```bash
    # Create the environment (named .venv)
    python3 -m venv .venv

    # Activate the environment
    source .venv/bin/activate
    ```
    You should see `(.venv)` appear at the beginning of your terminal prompt.

4.  **Install the required Python packages using `requirements.txt`:**
    Make sure your virtual environment is activated (if you created one).
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Open your terminal.**

2.  **Navigate to the project directory** where you cloned the repository:
    ```bash
    cd path/to/gpu_mon_qt
    ```

3.  **(If using a virtual environment) Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

5.  The GPU Monitor window should appear, displaying your GPU information and updating the status metrics every second.

    *   **Troubleshooting:** If the application shows "Error", "N/A", or doesn't start, ensure your NVIDIA drivers are correctly installed and the `nvidia-smi` command runs without errors in your terminal. Check the terminal output where you ran `python main.py` for specific error messages printed by the application (e.g., "nvidia-smi not found", "Error executing nvidia-smi").

## License

This project is licensed under the GNU GPL v3 license - see the LICENSE file for details.
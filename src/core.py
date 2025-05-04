# src/core.py
import subprocess
import re
import os # Needed for path joining
import sys # For sys.prefix (optional, for finding helper)
import shutil # For checking if helper exists in PATH

# Static info function
def get_gpu_static_info():
    """
    Gets static GPU information (Name, VRAM, Driver, Max PCIe Gen) using nvidia-smi.
    Assumes a single GPU for simplicity. Returns None on error.
    """
    try:
        query_items = ["gpu_name", "memory.total", "driver_version", "pcie.link.gen.max"]
        output_keys = ["name", "vram", "driver", "pcie_max_gen"]
        command = f"nvidia-smi --query-gpu={','.join(query_items)} --format=csv,noheader,nounits"
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True, timeout=5
        )
        output_line = result.stdout.strip().split('\n')[0]
        values = [v.strip() for v in output_line.split(',')]
        if len(values) == len(query_items):
            info = dict(zip(output_keys, values))
            info["vram"] = f"{info['vram']} MiB"
            return info
        else:
            print(f"Error parsing static info: Expected {len(query_items)} values, got {len(values)}. Output: '{output_line}'")
            return None
    except FileNotFoundError:
        print("Error: 'nvidia-smi' command not found (for static info).")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing nvidia-smi for static info: {e}\nStderr: {e.stderr.strip()}")
        return None
    except subprocess.TimeoutExpired:
        print("Error: nvidia-smi command for static info timed out.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in get_gpu_static_info: {e}")
        return None

# --- Updated function for ALL dynamic status data ---
def get_gpu_dynamic_status():
    """
    Gets dynamic GPU status (Temp, Util GPU/Mem, Mem Free/Used, Power, Clocks, Fan)
    using nvidia-smi. Assumes a single GPU for simplicity.

    Returns:
        dict: A dictionary containing status keys on success. Values are strings
              as returned by nvidia-smi (need parsing/unit adding later).
              Keys: 'temperature', 'gpu_util', 'mem_util', 'mem_free', 'mem_used',
                    'power', 'core_clock', 'mem_clock', 'fan_speed'
        None: If any error occurs during fetching or parsing.
    """
    try:
        # Define the properties to query - adding new items
        query_items = [
            "temperature.gpu",
            "utilization.gpu",
            "utilization.memory",
            "memory.free",
            "memory.used",
            "power.draw",             # Added
            "clocks.current.graphics",# Added
            "clocks.current.memory",  # Added
            "fan.speed"               # Added
        ]
        # Define keys for the output dictionary, matching the order of query_items
        output_keys = [
            "temperature",
            "gpu_util",
            "mem_util",
            "mem_free",
            "mem_used",
            "power",                  # Added
            "core_clock",             # Added
            "mem_clock",              # Added
            "fan_speed"               # Added
        ]

        command = f"nvidia-smi --query-gpu={','.join(query_items)} --format=csv,noheader,nounits"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            timeout=5 # Using a timeout
        )

        # Example output: 60, 10, 5, 6000, 2000, 55.12, 1500, 7000, 30
        output_line = result.stdout.strip().split('\n')[0]
        values = [v.strip() for v in output_line.split(',')]

        if len(values) == len(query_items):
            status = dict(zip(output_keys, values))
            # Handle potential "[N/A]" values which nvidia-smi might return
            # for certain fields (like fan speed on passively cooled cards)
            for key, value in status.items():
                if "[not supported]" in value.lower() or "[n/a]" in value.lower():
                     status[key] = "N/A" # Standardize missing value representation
            return status
        else:
            print(f"Error parsing dynamic status: Expected {len(query_items)} values, got {len(values)}. Output: '{output_line}'")
            return None

    except FileNotFoundError:
        print("Error: 'nvidia-smi' command not found (for dynamic status).")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing nvidia-smi for dynamic status: {e}\nStderr: {e.stderr.strip()}")
        return None
    except subprocess.TimeoutExpired:
        print("Error: nvidia-smi command for dynamic status timed out.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in get_gpu_dynamic_status: {e}")
        return None

# --- Path to the compiled C helper ---
# Adjust this path as needed. Assumes gddr6_helper is in the same dir as core.py
HELPER_NAME = "gddr6_helper"
# Try to find it alongside the script first
HELPER_PATH = os.path.join(os.path.dirname(__file__), HELPER_NAME)
# Fallback: Check if it's in the system PATH (if installed system-wide)
if not os.path.exists(HELPER_PATH) or not os.access(HELPER_PATH, os.X_OK):
    HELPER_PATH = shutil.which(HELPER_NAME) # None if not found in PATH


def get_vram_temperature():
    """
    Gets VRAM temperature by executing the compiled 'gddr6_helper' C program.

    REQUIRES:
        - The 'gddr6_helper' executable to be compiled and located at HELPER_PATH
          or in the system PATH.
        - The 'gddr6_helper' to be run with root privileges (e.g., via sudo).
        - libpci-dev installed for the helper compilation.

    Returns:
        int: VRAM temperature in degrees Celsius if successful.
        str: An error message ('N/A', 'No Helper', 'No Root?', 'Error', 'Not Supported')
             if the temperature cannot be retrieved. 'Not Supported' might mean
             the GPU isn't in the helper's table or mapping failed.
    """
    if HELPER_PATH is None:
        # print("VRAM Temp Error: gddr6_helper executable not found.")
        return "No Helper" # Helper program not found or not executable

    # Construct the command, prepending sudo
    command = ["sudo", "-n", HELPER_PATH] # -n: non-interactive sudo

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True, # Raise error on non-zero exit code from helper
            timeout=3  # Short timeout for the helper
        )

        # Parse the output (expecting a single integer)
        temp_str = result.stdout.strip()
        if not temp_str: # Handle empty output case
             print(f"VRAM Temp Error: Helper '{HELPER_PATH}' produced no output.")
             return "Error"

        temperature = int(temp_str)

        if temperature < 0: # Helper uses -1 for internal errors typically
             print(f"VRAM Temp Info: Helper indicated error or no compatible device (returned {temperature}).")
             # Could refine this based on specific negative return codes if added to C helper
             return "Not Supported"
        return temperature

    except FileNotFoundError:
        # This would catch if 'sudo' itself isn't found, highly unlikely
        print("VRAM Temp Error: 'sudo' command not found?")
        return "Error"
    except subprocess.CalledProcessError as e:
        # Helper exited with a non-zero status
        stderr_output = e.stderr.strip()
        # Check if it's likely a sudo password prompt failure
        if "password is required" in stderr_output or "incorrect password attempt" in stderr_output or "sudo: a password is required" in stderr_output:
            print("VRAM Temp Error: sudo requires a password or failed authentication.")
            return "No Root?"
        elif "Root privileges required" in stderr_output:
            print("VRAM Temp Error: Helper explicitly requires root (sudo might have failed).")
            return "No Root?"
        elif "Memory mapping failed" in stderr_output:
             print(f"VRAM Temp Error: Helper failed to map memory.\nStderr: {stderr_output}")
             return "Not Supported" # Likely incompatible or requires kernel param
        elif "Could not open /dev/mem" in stderr_output:
             print(f"VRAM Temp Error: Helper could not open /dev/mem.\nStderr: {stderr_output}")
             return "No Root?" # Could be permissions or other issue
        else:
            # Other errors from the helper
            print(f"VRAM Temp Error: Helper exited with status {e.returncode}.")
            if stderr_output:
                print(f"  Stderr: {stderr_output}")
            else:
                print("  Stderr: (empty)")
            return "Error" # General helper error

    except subprocess.TimeoutExpired:
        print(f"VRAM Temp Error: Helper command '{' '.join(command)}' timed out.")
        # Attempt to kill the process if possible (may need pid, complex)
        return "Timeout"
    except ValueError:
        # Output wasn't a valid integer
        print(f"VRAM Temp Error: Cannot parse helper output '{result.stdout.strip()}' as integer.")
        return "Parse Err"
    except Exception as e:
        # Catch-all for other unexpected Python errors
        print(f"An unexpected Python error occurred in get_vram_temperature: {e}")
        return "Py Error"


# --- Optional: For testing core.py directly ---
if __name__ == "__main__":
    print("--- Testing Static Info ---")
    # ... (static test remains same) ...

    print("\n--- Testing Dynamic Status ---")
    # ... (dynamic status test remains same) ...

    print("\n--- Testing VRAM Temperature (Requires sudo & helper) ---")
    vram_temp = get_vram_temperature()
    if isinstance(vram_temp, int):
        print(f"  VRAM Temperature: {vram_temp}°C")
    else:
        print(f"  Could not get VRAM Temperature. Status: {vram_temp}")
        if vram_temp == "No Root?":
            print("  -> Hint: Configure passwordless sudo for the helper:")
            print(f"     echo '$USER ALL=(ALL) NOPASSWD: {HELPER_PATH}' | sudo EDITOR='tee -a' visudo")
            print(f"     (Replace $USER with your username if needed, verify path is correct)")

# --- Optional: For testing core.py directly ---
if __name__ == "__main__":
    print("--- Testing Static Info ---")
    static_info = get_gpu_static_info()
    if static_info:
        print(f"  GPU Name: {static_info['name']}")
        print(f"  VRAM: {static_info['vram']}")
        print(f"  Driver Version: {static_info['driver']}")
        print(f"  Max PCIe Gen: {static_info['pcie_max_gen']}")
    else:
        print("  Could not get static GPU info.")

    print("\n--- Testing Dynamic Status ---")
    dynamic_status = get_gpu_dynamic_status()
    if dynamic_status:
        print(f"  Temperature: {dynamic_status.get('temperature', '?')} °C")
        print(f"  GPU Utilization: {dynamic_status.get('gpu_util', '?')} %")
        print(f"  Memory Utilization: {dynamic_status.get('mem_util', '?')} %")
        print(f"  Memory Free: {dynamic_status.get('mem_free', '?')} MiB")
        print(f"  Memory Used: {dynamic_status.get('mem_used', '?')} MiB")
        print(f"  Power Draw: {dynamic_status.get('power', '?')} W")         # Added test
        print(f"  Core Clock: {dynamic_status.get('core_clock', '?')} MHz")   # Added test
        print(f"  Memory Clock: {dynamic_status.get('mem_clock', '?')} MHz") # Added test
        print(f"  Fan Speed: {dynamic_status.get('fan_speed', '?')} %")       # Added test
    else:
        print("  Could not get dynamic GPU status.")
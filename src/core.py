# src/core.py
import subprocess
import re

# Static info function remains the same
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
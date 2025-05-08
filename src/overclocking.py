# overclocking.py
import subprocess
import re
import logging
import shlex
import os
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# (run_nv_settings_command, run_smi_command, parse_nvidia_smi_output, check_coolbits_features_enabled remain the same)
# --- run_nv_settings_command ---
def run_nv_settings_command(command_list):
    # (Implementation from previous version)
    try:
        env = os.environ.copy()
        if not env.get('DISPLAY'): logging.warning("DISPLAY not set. nvidia-settings might fail.")
        result = subprocess.run(command_list, capture_output=True, text=True, timeout=10, env=env)
        if result.returncode != 0:
            stderr_lower = result.stderr.lower()
            if "attribute" in stderr_lower and ("not available" in stderr_lower or "isn't available" in stderr_lower): return None, "Attribute not available"
            elif "does not exist" in stderr_lower: return None, "Target does not exist"
            elif "failed to connect" in stderr_lower or "unable to init server" in stderr_lower or "cannot open display" in stderr_lower: return None, "X Server connection failed"
            elif "control display is undefined" in stderr_lower: return None, "Control display undefined"
            else: return None, result.stderr.strip()
        return result.stdout.strip(), None
    except FileNotFoundError: return None, "'nvidia-settings' not found"
    except subprocess.TimeoutExpired: return None, "Command timed out"
    except Exception as e: return None, f"Unexpected error: {e}"

# --- run_smi_command ---
def run_smi_command(command):
    # (Implementation from previous version)
    try:
        if isinstance(command, str): command_list = shlex.split(command)
        else: command_list = command
        result = subprocess.run(command_list, check=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), None
    except FileNotFoundError: return None, f"Command '{command_list[0]}' not found."
    except subprocess.CalledProcessError as e: return None, f"nvidia-smi error: {e.stderr.strip()}"
    except subprocess.TimeoutExpired: return None, "Command timed out"
    except Exception as e: return None, f"Unexpected error: {e}"

# --- parse_nvidia_smi_output ---
def parse_nvidia_smi_output(output, patterns):
    # (Implementation from previous version)
    if output is None: return {key: None for key in patterns}
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if match:
            value = match.group(1) if match.groups() else match.group(0)
            cleaned_value = re.sub(r'\s*(?:W|MHz)\s*$', '', value).strip()
            try: results[key] = float(cleaned_value)
            except ValueError: results[key] = value
        else: results[key] = None
    return results

# --- check_coolbits_features_enabled ---
def check_coolbits_features_enabled(gpu_id=0, performance_level=3):
    # (Implementation from previous version)
    logging.info(f"Checking Coolbits features for GPU {gpu_id} using nvidia-settings -t -q...")
    attribute = f"[gpu:{gpu_id}]/GPUGraphicsClockOffset[{performance_level}]"
    command = ["nvidia-settings", "-t", "-q", attribute]
    output, error_msg = run_nv_settings_command(command)
    if error_msg == "Attribute not available": return False
    elif error_msg: return False
    elif output is not None: return True
    else: return False

# --- get_gpu_overclock_info (MODIFIED: Added default power limit query) ---
def get_gpu_overclock_info(gpu_id=0, performance_level=3):
    logging.info(f"Querying overclock info for GPU {gpu_id}")
    gpu_info = {}
    coolbits_ok = check_coolbits_features_enabled(gpu_id, performance_level)
    gpu_info['coolbits_enabled'] = coolbits_ok
    # (Handle coolbits not ok case)
    if not coolbits_ok:
         logging.warning("Coolbits features check failed. Reporting defaults.")
         DEFAULT_CORE_MIN, DEFAULT_CORE_MAX = -500, 2000; DEFAULT_MEM_MIN, DEFAULT_MEM_MAX = -500, 3000
         gpu_info.update({ 'power_limit_current': None, 'power_limit_min': None, 'power_limit_max': None, 'power_limit_default': None, 'core_offset_current': 0, 'core_offset_min': DEFAULT_CORE_MIN, 'core_offset_max': DEFAULT_CORE_MAX, 'memory_offset_current': 0, 'memory_offset_min': DEFAULT_MEM_MIN, 'memory_offset_max': DEFAULT_MEM_MAX })
         return gpu_info

    # Power Limits (nvidia-smi)
    power_output, error = run_smi_command(f"nvidia-smi -i {gpu_id} -q -d POWER")
    if power_output:
        power_patterns = {
            'power_limit_current': r"Power Limit\s+:\s+([\d\.]+)\s+W",
            'power_limit_min': r"Min Power Limit\s+:\s+([\d\.]+)\s+W",
            'power_limit_max': r"Max Power Limit\s+:\s+([\d\.]+)\s+W",
            # *** ADDED Default Power Limit ***
            'power_limit_default': r"Default Power Limit\s+:\s+([\d\.]+)\s+W",
        }
        gpu_info.update(parse_nvidia_smi_output(power_output, power_patterns))
    else:
        logging.error(f"Failed to get power data via nvidia-smi: {error}")
        gpu_info.update({'power_limit_current': None, 'power_limit_min': None, 'power_limit_max': None, 'power_limit_default': None}) # Ensure default is None on error

    # (Rest of Clock Offset query logic remains the same as previous successful version)
    # Defaults
    DEFAULT_CORE_MIN, DEFAULT_CORE_MAX = -500, 2000; DEFAULT_MEM_MIN, DEFAULT_MEM_MAX = -500, 3000
    gpu_info.setdefault('core_offset_current', 0); gpu_info.setdefault('core_offset_min', DEFAULT_CORE_MIN); gpu_info.setdefault('core_offset_max', DEFAULT_CORE_MAX)
    gpu_info.setdefault('memory_offset_current', 0); gpu_info.setdefault('memory_offset_min', DEFAULT_MEM_MIN); gpu_info.setdefault('memory_offset_max', DEFAULT_MEM_MAX)
    # ... Clock offset reading logic ...
    core_attr = f"[gpu:{gpu_id}]/GPUGraphicsClockOffset[{performance_level}]"; mem_attr = f"[gpu:{gpu_id}]/GPUMemoryTransferRateOffset[{performance_level}]"
    cmd_core_current = ["nvidia-settings", "-t", "-q", core_attr]; output_core_tq, err_core_tq = run_nv_settings_command(cmd_core_current)
    if output_core_tq is not None and not err_core_tq:
        try: gpu_info['core_offset_current'] = int(output_core_tq)
        except ValueError: logging.error(f"Could not parse core offset '{output_core_tq}' to int.")
    else: logging.warning(f"Failed query current core offset: {err_core_tq}")
    cmd_core_limits = ["nvidia-settings", "-q", core_attr]; output_core_q, err_core_q = run_nv_settings_command(cmd_core_limits)
    if output_core_q and not err_core_q:
        pattern = r"Valid\s+values\s+for\s+'GPUGraphicsClockOffset'\s+are\s+in\s+the\s+range\s+(-?\d+)\s+-\s+(\d+)|Valid values range from\s+(-?\d+)\s+to\s+(\d+)"; match_limits = re.search(pattern, output_core_q, re.IGNORECASE | re.MULTILINE)
        if match_limits:
            try: g1, g2, g3, g4 = match_limits.groups(); gpu_info['core_offset_min'] = int(g1 if g1 else g3); gpu_info['core_offset_max'] = int(g2 if g2 else g4)
            except Exception as e: logging.error(f"Error parsing regex groups for core limits: {e}")
        else: logging.warning(f"Could not parse core offset limits using regex.")
    else: logging.warning(f"Failed query core offset limits: {err_core_q}")
    cmd_mem_current = ["nvidia-settings", "-t", "-q", mem_attr]; output_mem_tq, err_mem_tq = run_nv_settings_command(cmd_mem_current)
    if output_mem_tq is not None and not err_mem_tq:
        try: gpu_info['memory_offset_current'] = int(output_mem_tq)
        except ValueError: logging.error(f"Could not parse memory offset '{output_mem_tq}' to int.")
    else: logging.warning(f"Failed query current memory offset: {err_mem_tq}")
    cmd_mem_limits = ["nvidia-settings", "-q", mem_attr]; output_mem_q, err_mem_q = run_nv_settings_command(cmd_mem_limits)
    if output_mem_q and not err_mem_q:
        pattern = r"Valid\s+values\s+for\s+'GPUMemoryTransferRateOffset'\s+are\s+in\s+the\s+range\s+(-?\d+)\s+-\s+(\d+)|Valid values range from\s+(-?\d+)\s+to\s+(\d+)"; match_limits = re.search(pattern, output_mem_q, re.IGNORECASE | re.MULTILINE)
        if match_limits:
            try: g1, g2, g3, g4 = match_limits.groups(); gpu_info['memory_offset_min'] = int(g1 if g1 else g3); gpu_info['memory_offset_max'] = int(g2 if g2 else g4)
            except Exception as e: logging.error(f"Error parsing regex groups for memory limits: {e}")
        else: logging.warning(f"Could not parse memory offset limits using regex.")
    else: logging.warning(f"Failed query memory offset limits: {err_mem_q}")


    # Final default assignment logic (Add power_limit_default)
    essential_keys_with_defaults = {
        'coolbits_enabled': False,
        'power_limit_current': None, 'power_limit_min': None, 'power_limit_max': None, 'power_limit_default': None, # Added default
        'core_offset_current': 0, 'core_offset_min': DEFAULT_CORE_MIN, 'core_offset_max': DEFAULT_CORE_MAX,
        'memory_offset_current': 0, 'memory_offset_min': DEFAULT_MEM_MIN, 'memory_offset_max': DEFAULT_MEM_MAX
    }
    final_gpu_info = {}
    for k, default_val in essential_keys_with_defaults.items():
        final_gpu_info[k] = gpu_info.get(k, default_val)
        if final_gpu_info[k] is None and default_val is not None:
             # Apply numeric defaults if value ended up None
             if k in ['core_offset_current', 'memory_offset_current', 'core_offset_min', 'core_offset_max', 'memory_offset_min', 'memory_offset_max']:
                 final_gpu_info[k] = default_val
    logging.info(f"Final GPU Info: {final_gpu_info}")
    return final_gpu_info

# --- apply_clock_offset ---
def apply_clock_offset(gpu_id, clock_type, offset_mhz):
    # (Implementation from previous version)
    if clock_type == 'core': attribute = f"[gpu:{gpu_id}]/GPUGraphicsClockOffsetAllPerformanceLevels"
    elif clock_type == 'memory': attribute = f"[gpu:{gpu_id}]/GPUMemoryTransferRateOffsetAllPerformanceLevels"
    else: return False, "Invalid clock type specified."
    display = os.environ.get('DISPLAY'); xauthority = os.environ.get('XAUTHORITY')
    if not display: return False, "Error: DISPLAY not found."
    if not xauthority: default_xauth = os.path.expanduser("~/.Xauthority"); xauthority = default_xauth if os.path.exists(default_xauth) else None
    if not xauthority: return False, "Error: XAUTHORITY not found and default missing."
    command = [ "pkexec", "env", f"DISPLAY={display}", f"XAUTHORITY={xauthority}", "nvidia-settings", "-a", f"{attribute}={offset_mhz}" ]
    logging.info(f"Attempting to run: {' '.join(shlex.quote(arg) for arg in command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            stderr_lower = result.stderr.lower()
            if "authorization required" in stderr_lower or "no authorization protocol specified" in stderr_lower: return False, f"Error: X Authentication failed. Stderr: {result.stderr.strip()}" # Treat as error
            elif not result.stderr.strip(): msg = f"{clock_type.capitalize()} offset set to {offset_mhz} MHz."; return True, msg
            else: msg = f"{clock_type.capitalize()} offset set {offset_mhz} MHz (warnings: {result.stderr.strip()})."; logging.warning(msg); return True, msg
        else: # Failure
            error_msg = result.stderr.strip(); stderr_lower = error_msg.lower()
            if result.returncode == 126: msg = "Error: pkexec auth failed."
            elif "authorization required" in stderr_lower or "cannot open display" in stderr_lower: msg = f"Error: X Auth failed. Stderr: {error_msg}"
            elif "Attribute" in error_msg and "not available" in error_msg: msg = f"Error: Attribute '{attribute}' not available?"
            elif "Valid values" in error_msg: msg = f"Error: Invalid value. {error_msg}"
            else: msg = f"Failed to set offset. Code: {result.returncode}. Stderr: {error_msg}"
            logging.error(msg); return False, msg
    except FileNotFoundError: msg = "Error: pkexec/env/nvidia-settings not found." ; logging.error(msg); return False, msg
    except subprocess.TimeoutExpired: msg = "Error: Command timed out."; logging.error(msg); return False, msg
    except Exception as e: msg = f"An unexpected error occurred: {e}"; logging.error(msg); return False, msg

# --- apply_power_limit ---
def apply_power_limit(gpu_id, power_limit_watts):
    # (Implementation from previous version)
    if not isinstance(power_limit_watts, (int, float)) or power_limit_watts <= 0: return False, "Invalid power limit value."
    command = [ "pkexec", "nvidia-smi", "-i", str(gpu_id), "-pl", str(power_limit_watts) ]
    logging.info(f"Attempting to run: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            if "successfully" in result.stdout.lower(): msg = f"Power limit set to {power_limit_watts}W."; return True, msg
            elif not result.stderr.strip(): msg = f"Power limit command executed for {power_limit_watts}W."; return True, msg
            else: msg = f"Power limit executed {power_limit_watts}W (warnings: {result.stderr.strip()})."; logging.warning(msg); return True, msg
        else:
            error_msg = result.stderr.strip()
            if result.returncode == 127: msg = f"Error: pkexec/nvidia-smi not found."
            elif result.returncode == 126: msg = "Error: Auth failed."
            elif "Persistence Mode is disabled" in error_msg: msg = "Error: Persistence Mode required."
            else: msg = f"Failed power limit. Code: {result.returncode}. Stderr: {error_msg}"
            logging.error(msg); return False, msg
    except FileNotFoundError: msg = "Error: 'pkexec' not found."; logging.error(msg); return False, msg
    except subprocess.TimeoutExpired: msg = "Error: Command timed out."; logging.error(msg); return False, msg
    except Exception as e: msg = f"An unexpected error occurred: {e}"; logging.error(msg); return False, msg

# --- Example Usage ---
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG) # Set debug for testing
    # (System info printout remains the same)
    print("\nTesting overclocking.py with Coolbits check (DEBUG level)...")
    info = get_gpu_overclock_info(gpu_id=0)
    if info:
        coolbits_active = info.get('coolbits_enabled')
        print(f"\nCoolbits Features Enabled Check: {coolbits_active}")
        if not coolbits_active: print("\n--- Coolbits INSTRUCTIONS ---\n(Omitted)\n---------------------------")
        print("\n--- GPU Overclock Info (GPU 0) ---")
        for key, value in info.items(): print(f"{key.replace('_', ' ').title()}: {value if value is not None else 'N/A'}")
        print("----------------------------------")
        # Test applying settings
        if coolbits_active:
             current_core_offset = info.get('core_offset_current', 0)
             if current_core_offset is not None:
                  test_core_offset = current_core_offset - 77 # Try setting different offset
                  print(f"\nAttempting to set CORE offset to {test_core_offset} MHz using AllPerformanceLevels...")
                  # *** Call without performance_level ***
                  success, message = apply_clock_offset(0, 'core', test_core_offset)
                  print(f"Result: {success} - {message}")
                  if success:
                       print("Attempting to set CORE offset back...")
                       import time; time.sleep(0.5)
                       apply_clock_offset(0, 'core', current_core_offset) # Set back
        else: print("\nSkipping offset apply tests as Coolbits not detected.")
        # (Power limit test code...)
    else: print("\nFailed to retrieve any overclocking information.")
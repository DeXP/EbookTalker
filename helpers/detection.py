# core/detection.py
import sys
import subprocess
import ctypes

def is_process_elevated() -> bool:
    if sys.platform != "win32":
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def detect_nvidia_gpu() -> str:
    if sys.platform != "win32":
        return "cpu"
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and result.stdout.strip():
            name = result.stdout.strip().lower()
            if "rtx" in name or "a100" in name or "a40" in name:
                return "cuda129"
            elif "gtx 10" in name:
                return "cuda126"
    except:
        pass
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "Name"],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                lname = line.strip().lower()
                if "nvidia" in lname and lname != "name":
                    if "rtx" in lname:
                        return "cuda129"
                    elif "gtx 10" in lname:
                        return "cuda126"
            return "cpu"
    except:
        pass
    return "cpu"

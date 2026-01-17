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
    
    # Try nvidia-smi first
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and result.stdout.strip():
            name = result.stdout.strip().lower()
            # Explicitly map known architectures
            if any(arch in name for arch in ["rtx 40", "a100", "a40", "l4", "h100"]):
                return "cuda130"
            elif any(arch in name for arch in [
                "rtx 30", "rtx 20", "gtx 10", "gtx 16",
                "titan rtx", "quadro rtx", "tesla t4", "a2", "a10"
            ]):
                return "cuda126"
            else:
                # Unknown NVIDIA GPU — do not assume compatibility
                return "cpu"
    except Exception:
        pass

    # Fallback to WMIC
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
                    if any(arch in lname for arch in ["rtx 40", "a100", "a40", "l4", "h100"]):
                        return "cuda130"
                    elif any(arch in lname for arch in [
                        "rtx 30", "rtx 20", "gtx 10", "gtx 16",
                        "titan rtx", "quadro rtx", "tesla t4", "a2", "a10"
                    ]):
                        return "cuda126"
                    else:
                        # Detected NVIDIA but not in known list → conservative fallback
                        return "cpu"
            # No NVIDIA GPU found in WMIC output
            return "cpu"
    except Exception:
        pass

    return "cpu"

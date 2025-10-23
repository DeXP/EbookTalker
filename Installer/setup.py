import sys
from pathlib import Path
from cx_Freeze import setup, Executable

# --- Project layout ---
# ProjectRoot/
# ├── desktop.py
# ├── converter.py
# ├── static/
# ├── silero_stress/
# └── Installer/
#     └── setup.py   <-- this file

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

ENTRY_POINT = PROJECT_ROOT / "desktop.py"
ICON_PATH = PROJECT_ROOT / "static" / "favicon.ico"
SILERO_DIR = PROJECT_ROOT / "silero_stress"

APP_NAME = "EbookTalker"
DIST_PATH = PROJECT_ROOT / "dist"

# Ensure all paths exist (optional but helpful for debugging)
assert ENTRY_POINT.exists(), f"Entry point not found: {ENTRY_POINT}"
assert ICON_PATH.exists(), f"Icon not found: {ICON_PATH}"
assert SILERO_DIR.exists(), f"Silero directory not found: {SILERO_DIR}"

# --- Build options ---
build_exe_options = {
    #"includes": ["converter"],  # ✅ Explicitly include your local module
    "packages": [],             # add other hidden imports if needed
    "excludes": [],             # e.g., ["tkinter", "unittest"]
    "include_files": [
        # (PROJECT_ROOT / "converter.py", "converter.py"),
        #(SILERO_DIR, "silero_stress"),
        # Add more as needed, e.g.:
        # (PROJECT_ROOT / "config.ini", "config.ini"),
    ],
    "build_exe": DIST_PATH / APP_NAME,
}

# --- MSI options ---
bdist_msi_options = {
    "upgrade_code": "{e9074654-5750-492c-82ac-f7bf7ec91077}",
    "add_to_path": False,
    "initial_target_dir": r"[LocalAppDataFolder]\DeXPeriX\EbookTalker",
    "target_name": APP_NAME + ".msi",
}

# --- Executable ---
base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        script=str(ENTRY_POINT),
        target_name=APP_NAME + ".exe",
        base=base,
        icon=str(ICON_PATH),
    )
]

# --- Version ---
def get_version():
    version_file = PROJECT_ROOT / "static" / "version.txt"
    if version_file.exists():
        return version_file.read_text().strip()
    return "1.0.0"

setup(
    name=APP_NAME,
    version=get_version(),
    description="EbookTalker by DeXPeriX",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
import os, sys, json, shutil, subprocess
from pathlib import Path

# --- Configuration ---
APP_NAME = "EbookTalker"
EXE_NAME = f"{APP_NAME}.exe"
OUTPUT_MSI = f"{APP_NAME}.msi"
PRODUCER_NAME = "DeXPeriX"

OUTPUT_DIR = Path(__file__).parent.parent.parent.resolve()
ROOT_DIR = Path(__file__).parent.parent.resolve()
STATIC_DIR = ROOT_DIR / "static"
VERSION_FILE_PATH = STATIC_DIR / "version.txt"
ICON_PATH = STATIC_DIR / "favicon.ico"
SPLASH_PATH = STATIC_DIR / "splash.png"
I18N_SRC = STATIC_DIR / "i18n"
RC_OUTPUT_PATH = ROOT_DIR / "data" / "tmp" / "versionInfo.rc"
ENTRY_POINT = ROOT_DIR / "desktop.py"
CONFIG_FILE = ROOT_DIR / "default.cfg"
DIST_PATH = OUTPUT_DIR / "EbookTalker-Win64"
ZIP_PATH = OUTPUT_DIR / "EbookTalker-Win64.zip"

EN_PATH = I18N_SRC / 'en.json'
RU_PATH = I18N_SRC / 'ru.json'

ARCH = "x64"  # or "x86" if your app is 32-bit
CULTURES = ["en-us", "ru-ru"]
WIX_OBJ_FILES = ["Product.wixobj", "Files.wixobj"]
HEAT_EXE = "C:\\Program Files\\WiX Toolset v6.0\\bin\\x64\\heat.exe"


# === Helper functions ===
def generate_rc(en, ru, comma_version, raw_version):
    return f'''# UTF-8
    #
    # For more details about fixed file info 'ffi' see:
    # https://learn.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource

    VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=({comma_version}),
        prodvers=({comma_version}),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
        [
            StringTable(
            '040904b0',
            [
                StringStruct('CompanyName', '{PRODUCER_NAME}'),
                StringStruct('FileDescription', '{en["appDescription"]}'),
                StringStruct('FileVersion', '{raw_version}'),
                StringStruct('InternalName', '{en["appTitle"]}'),
                StringStruct('LegalCopyright', '{en["LegalCopyright"]}'),
                StringStruct('OriginalFilename', '{EXE_NAME}'),
                StringStruct('ProductName', '{en["appTitle"]}'),
                StringStruct('ProductVersion', '{raw_version}')
            ]
            ),
            StringTable(
            '041904b0',
            [
                StringStruct('CompanyName', '{PRODUCER_NAME}'),
                StringStruct('FileDescription', '{ru["appDescription"]}'),
                StringStruct('FileVersion', '{raw_version}'),
                StringStruct('InternalName', '{ru["appTitle"]}'),
                StringStruct('LegalCopyright', '{ru["LegalCopyright"]}'),
                StringStruct('OriginalFilename', '{EXE_NAME}'),
                StringStruct('ProductName', '{ru["appTitle"]}'),
                StringStruct('ProductVersion', '{raw_version}')
            ]
            )
        ]
        ),
        VarFileInfo([
        VarStruct('Translation', [1033, 1200]),
        VarStruct('Translation', [1049, 1200])
        ])
    ]
    )'''


def run_cmd(cmd, cwd=None):
    """Run a shell command and raise on error."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {' '.join(cmd)}", file=sys.stderr)
        sys.exit(result.returncode)


def ensure_wix_installed():
    """Check if wix.exe is available."""
    try:
        subprocess.run(["wix", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ WiX Toolset v4+ (wix.exe) not found. Please install it from https://wixtoolset.org/", file=sys.stderr)
        sys.exit(1)


# === Main build logic ===
def main():

    en = json.loads(EN_PATH.read_text(encoding='utf8'))
    ru = json.loads(RU_PATH.read_text(encoding='utf8'))

    # --- Step 1: Read version and generate RC file ---
    raw_version = VERSION_FILE_PATH.read_text().strip()
    version = raw_version
    while version.count('.') < 3:
        version += '.0'

    comma_version = version.replace('.', ',')

    RC_OUTPUT_PATH.write_text(generate_rc(en, ru, comma_version, raw_version), encoding='utf8')

    # --- Step 2: Build with PyInstaller (using Python API) ---
    from PyInstaller.__main__ import run as pyinstaller_run

    pyinstaller_args = [
        str(ENTRY_POINT),
        "--name", APP_NAME,
        "--noconfirm",
        "--noupx",
        "--onedir",
        "--windowed",
        "--distpath", str(DIST_PATH),
        "--icon", str(ICON_PATH),
        "--splash", str(SPLASH_PATH),
        "--add-data", "silero_stress;silero_stress",
        "--version-file", str(RC_OUTPUT_PATH)
    ]

    pyinstaller_run(pyinstaller_args)

    # --- Step 3: Post-build file operations ---
    dist_app_dir = DIST_PATH / APP_NAME

    # Copy i18n files
    i18n_dest = DIST_PATH / "static" / "i18n"
    shutil.rmtree(i18n_dest, ignore_errors=True)
    shutil.copytree(I18N_SRC, i18n_dest)

    # Copy config file
    shutil.copy2(CONFIG_FILE, DIST_PATH / CONFIG_FILE.name)

    # Move executable to root
    exe_src = dist_app_dir / EXE_NAME
    if exe_src.exists():
        exe_dest = DIST_PATH / EXE_NAME
        if exe_dest.exists():
            exe_dest.unlink()
        shutil.move(exe_src, exe_dest)

    # Move _internal directory
    internal_src = dist_app_dir / "_internal"
    if internal_src.exists():
        internal_dest = DIST_PATH / "_internal"
        if internal_dest.exists():
            shutil.rmtree(internal_dest)
        shutil.move(internal_src, internal_dest)

    # Remove old app directory
    if dist_app_dir.exists():
        shutil.rmtree(dist_app_dir)

    # --- Step 4: Clean up zip file ---
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print(f"Creating ZIP archive: {ZIP_PATH}")
    shutil.make_archive(
        base_name=ZIP_PATH.with_suffix(''),
        format='zip',
        root_dir=DIST_PATH
    )


    # MSI
    print(f"📦 Building {APP_NAME} MSI installer...\n")

    # Ensure WiX is available
    ensure_wix_installed()

    # Clean previous outputs
    print("🧹 Cleaning previous build artifacts...")
    for pattern in ["*.wixobj", "*.msi", "Files.wxs"]:
        for f in Path(".").glob(pattern):
            if f.is_file():
                f.unlink()
                print(f"   Removed {f}")

    # Step 1: Harvest files with heat (via wix harvest)
    print("\n🔍 Harvesting application files with WiX...")
    run_cmd([
        HEAT_EXE, "dir",
        str(DIST_PATH),
        "-o", "Files.wxs",
        "-cg", "AppFiles",
        "-var", "var.SourceDir",  # Note: use 'var.SourceDir' for -var
        "-sfrag", "-sreg", "-suid", "-gg",
        "-platform", ARCH  # ensures correct component attributes
    ])

    # Step 2: Build MSI
    print("\n🔨 Building MSI installer...")
    cmd = [
        "wix", "build",
        "Product.wxs", "Files.wxs",
        "-ext", "WixToolset.UI.wixext",
        "-ext", "WixToolset.Util.wixext",
        "-bindpath", f"SourceDir={DIST_PATH}",
        "-culture", ";".join(CULTURES),
        "-arch", ARCH,
        "-out", OUTPUT_MSI
    ]
    run_cmd(cmd)

    print(f"\n✅ Success! Installer created: {Path(OUTPUT_MSI).resolve()}")



if __name__ == "__main__":
    main()
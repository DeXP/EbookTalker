#!/usr/bin/python3

import sys, json, shutil, subprocess
from pathlib import Path

# --- Configuration ---
APP_NAME = "EbookTalker"
EXE_NAME = f"{APP_NAME}.exe"
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
CFG_DIR = ROOT_DIR / "cfg"
INSTALLER_SCRIPT = CFG_DIR / "installer.nsi"
PORTABLE_CONFIG_FILE = ROOT_DIR / "default.cfg"
INSTALLER_CONFIG_FILE = CFG_DIR / "installer.cfg"
DIST_PATH = OUTPUT_DIR / "EbookTalker-Win64"
DIST_DATA_PATH = DIST_PATH / "data"
DIST_SETTINGS_PATH = DIST_PATH / "settings.ini"

EN_PATH = I18N_SRC / 'en.json'
RU_PATH = I18N_SRC / 'ru.json'



# === Helper functions ===
def generate_rc(en, ru, comma_version, version):
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
            StringStruct('FileVersion', '{version}'),
            StringStruct('InternalName', '{en["appTitle"]}'),
            StringStruct('LegalCopyright', '{en["LegalCopyright"]}'),
            StringStruct('OriginalFilename', '{EXE_NAME}'),
            StringStruct('ProductName', '{en["appTitle"]}'),
            StringStruct('ProductVersion', '{version}')
        ]
        ),
        StringTable(
        '041904b0',
        [
            StringStruct('CompanyName', '{PRODUCER_NAME}'),
            StringStruct('FileDescription', '{ru["appDescription"]}'),
            StringStruct('FileVersion', '{version}'),
            StringStruct('InternalName', '{ru["appTitle"]}'),
            StringStruct('LegalCopyright', '{ru["LegalCopyright"]}'),
            StringStruct('OriginalFilename', '{EXE_NAME}'),
            StringStruct('ProductName', '{ru["appTitle"]}'),
            StringStruct('ProductVersion', '{version}')
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


def ensure_nsis_installed():
    try:
        subprocess.run(["makensis", "/VERSION"], capture_output=True, check=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ NSIS (makensis) not found. Install from https://nsis.sourceforge.io/Download", file=sys.stderr)
        sys.exit(1)




def create_exe():
    from PyInstaller.__main__ import run as pyinstaller_run

    # Clean temp dev files
    if DIST_DATA_PATH.exists():
        shutil.rmtree(DIST_DATA_PATH)

    if DIST_SETTINGS_PATH.exists():
        DIST_SETTINGS_PATH.unlink()

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
        "--collect-data", "silero_stress",
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
    shutil.copy2(PORTABLE_CONFIG_FILE, DIST_PATH / PORTABLE_CONFIG_FILE.name)

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



def create_zip(version):
    ZIP_PATH = OUTPUT_DIR / f"{APP_NAME}-{version}-win64-Portable.zip"

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print(f"\n🗜️ Creating ZIP archive: {ZIP_PATH}")
    shutil.make_archive(base_name=ZIP_PATH.with_suffix(''), format='zip', root_dir=DIST_PATH)



def create_installer(version, full_version, en, ru):
    OUTPUT_EXE = OUTPUT_DIR  / f"{APP_NAME}-{version}-win64.exe"

    # MSI
    print(f"\n📦 Building {APP_NAME} installer...\n")

    # Ensure NSIS is available
    ensure_nsis_installed()

    # Copy config file
    shutil.copy2(INSTALLER_CONFIG_FILE, DIST_PATH / PORTABLE_CONFIG_FILE.name)

    source_dir = DIST_PATH.resolve()

     # Pass VERSION and SOURCE_DIR as defines to NSIS
    cmd = [
        "makensis",
        f"-DVERSION={version}",
        f"-DBIGVERSION={full_version}",
        f"-DSOURCE_DIR={source_dir}",
        f"-DOUT={OUTPUT_EXE}",
        f"-DCOPYRIGHT={en["LegalCopyright"]}",
        f"-DAPP_NAME_EN={en["appTitle"]}",
        f"-DAPP_NAME_RU={ru["appTitle"]}",
        f"-DDESCRIPTION_EN={APP_NAME} - {en["appDescription"]}",
        f"-DDESCRIPTION_RU={APP_NAME} - {ru["appDescription"]}",
        str(INSTALLER_SCRIPT)
    ]
    
    result = subprocess.run(cmd, cwd=CFG_DIR, text=True)
    if result.returncode != 0:
        print("❌ NSIS build failed.", file=sys.stderr)
        sys.exit(1)

    # Copy back portable config file - so the folder is usable
    shutil.copy2(PORTABLE_CONFIG_FILE, DIST_PATH / PORTABLE_CONFIG_FILE.name)

    if OUTPUT_EXE.exists():
        size_mb = OUTPUT_EXE.stat().st_size / (1024 * 1024)
        print(f"✅ Success! {OUTPUT_EXE.name} ({size_mb:.1f} MB) ready.")
        print(f"   Silent install: .\\{OUTPUT_EXE.name} /S")
        print(f"   Package ID for winget: DeXPeriX.EbookTalker")
    else:
        print("❌ Output EXE not found.", file=sys.stderr)
        sys.exit(1)


# === Main build logic ===
def main():
    print(f"📖 {APP_NAME} Installer creator script")
    en = json.loads(EN_PATH.read_text(encoding='utf8'))
    ru = json.loads(RU_PATH.read_text(encoding='utf8'))

    # --- Step 1: Read version and generate RC file ---
    version = VERSION_FILE_PATH.read_text().strip()
    full_version = version
    while full_version.count('.') < 3:
        full_version += '.0'

    comma_version = full_version.replace('.', ',')

    RC_OUTPUT_PATH.write_text(generate_rc(en, ru, comma_version, version), encoding='utf8')
    print(f"\n📚 RC has been written to: {Path(RC_OUTPUT_PATH).resolve()}")

    if (len(sys.argv) < 2) or ('all' == sys.argv[1]):
        # Default - do all
        create_exe()
        create_zip(version)
        create_installer(version, full_version, en, ru)
    else:
        mode = str(sys.argv[1]).lower()

        if ('exe' == mode):
            create_exe()
        elif ('zip' == mode):
            create_zip(version)
        elif ('installer' == mode):
            create_installer(version, full_version, en, ru)
        elif ('-h' == mode) or ('/?' == mode) or ('h' == mode) or ('help' == mode) or ('--help' == mode):
            print("\nCall the script without arguments - all artifacts would be created. Or provide one of the following: exe, zip, installer")



def use_cz_freeze():
    import sys, json
    from pathlib import Path
    from cx_Freeze import setup, Executable

    sys.setrecursionlimit(sys.getrecursionlimit() * 5)

    APP_NAME = "EbookTalker"
    version = open("static/version.txt").read().strip()

    en = json.loads(Path("static/i18n/en.json").read_text(encoding='utf8'))

    build_exe_options = {
        # "packages": ["your_extra_modules"],
        "include_files": [
            ("D:\\ffmpeg", "ffmpeg"),
            ("models", "models"),
            ("jingle", "jingle"),
            ("static/i18n", "static/i18n"),
            ("static/book.png", "static/book.png"),
            ("static/favicon.ico", "static/favicon.ico"),
            ("LICENSE.md", "LICENSE.md"),
            ("cfg/installer.cfg", "default.cfg"),
        ],
        "include_msvcr": True
    }

    bdist_msi_options = {
        "upgrade_code": "{e9074654-5750-492c-82ac-f7bf7ec91077}",
        "add_to_path": False,
        "all_users": True,
        "initial_target_dir": f"[ProgramFiles64Folder]{APP_NAME}",
        "license_file": "info/license-gpl-3.0.rtf",
        "install_icon": "static/favicon.ico",
        "summary_data": {
            "author": "DeXPeriX"
        },
        "target_name": APP_NAME # f"{APP_NAME}-{version}-win-x64.msi",
    }

    #base = "Win32GUI" if sys.platform == "win32" else None
    base = "gui"

    setup(
        name=APP_NAME,
        version=version,
        description=APP_NAME,
        options={
            "build_exe": build_exe_options,
            "bdist_msi": bdist_msi_options,
        },
        executables=[Executable(
            script="desktop.py",
            target_name=APP_NAME,
            base=base, 
            icon="static/favicon"
        )],
    )


if __name__ == "__main__":
    main()
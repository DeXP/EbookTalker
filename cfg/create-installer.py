#!/usr/bin/python3

import os, sys, json, shutil, subprocess, hashlib, zipfile, py7zr
from pathlib import Path

# --- Configuration ---
APP_NAME = "EbookTalker"
EXE_NAME = f"{APP_NAME}.exe"
PRODUCER_NAME = "DeXPeriX"

GITHUB_REPO = "DeXP/EbookTalker"
LICENSE = "GPL-3.0"

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
DIST_INTERNAL_PATH = DIST_PATH / "_internal"

EN_PATH = I18N_SRC / 'en.json'
RU_PATH = I18N_SRC / 'ru.json'


# === Helper functions ===

# Render a modern Unicode progress bar string
def _render_progress(count: int, total: int, terminal_width: int = 80):
    if total <= 0:
        return ""
    percent = count / total
    info_text = f" {int(percent * 100)}% ({count}/{total})"
    info_width = len(info_text)
    bar_max_width = max(10, terminal_width - info_width - 2)  # 2 for brackets []
    bar_length = min(bar_max_width, max(0, terminal_width - info_width - 2))
    filled = int(bar_length * percent)
    GREEN, GRAY, RESET = '\033[32m', '\033[90m', '\033[0m' # ANSI color codes
    bar = GREEN + "█" * filled + GRAY + "░" * (bar_length - filled) + RESET
    return f"▕{bar}▏{info_text}"


# Get terminal width with fallback.
def _get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80
    

# Zip max compression with progressbar
def make_zip_with_max_compression(zip_path: Path, source_dir: Path):
    files = [f for f in source_dir.rglob('*') if f.is_file()]
    total = len(files)
    if total == 0:
        print("No files to archive.")
        return

    terminal_width = _get_terminal_width()
    count = 0

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file_path in files:
            arcname = file_path.relative_to(source_dir)
            zf.write(file_path, arcname)

            count += 1
            progress_str = _render_progress(count, total, terminal_width)
            sys.stdout.write(f"\r{progress_str}")
            sys.stdout.flush()

    sys.stdout.write('\n')


# py7zr stdout progressbar
def write_with_progress(archive: py7zr.SevenZipFile, src_root: Path, arc_root: str):
    files = [f for f in src_root.rglob('*') if f.is_file()]
    total = len(files)
    if total == 0:
        print("No files to archive.")
        return

    terminal_width = _get_terminal_width()
    count = 0

    for src_path in files:
        rel_path = src_path.relative_to(src_root)
        arc_path = Path(arc_root) / rel_path
        archive.write(src_path, arc_path.as_posix())

        count += 1
        progress_str = _render_progress(count, total, terminal_width)
        sys.stdout.write(f"\r{progress_str}")
        sys.stdout.flush()

    sys.stdout.write('\n')


# === Executable related functions ===
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


def calculate_sha256(file_path: Path) -> str:
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest().upper()



def create_exe(en: dict, ru: dict, version: str, full_version: str):
    # --- Step 1: Read version and generate RC file ---
    comma_version = full_version.replace('.', ',')

    RC_OUTPUT_PATH.write_text(generate_rc(en, ru, comma_version, version), encoding='utf8')
    print(f"\n📚 RC has been written to: {Path(RC_OUTPUT_PATH).resolve()}")

    # Clean temp dev files
    if DIST_DATA_PATH.exists():
        shutil.rmtree(DIST_DATA_PATH)

    if DIST_SETTINGS_PATH.exists():
        DIST_SETTINGS_PATH.unlink()

    # --- Step 2: Create exe with PyInstaller ---
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
        # "--collect-data", "TTS",
        # "--collect-data", "coqui-tts",
        "--add-data", "silero_stress:silero_stress",
        "--add-data", "ruaccent:ruaccent",
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



def extract_cuda():
    print(f"\n📟 Extracting CUDA plugin")
    import torch
    torch_version = str(torch.__version__)
    print(f"🔥 Torch {torch_version}")
    plugin_name = f"{APP_NAME}-Torch-{torch_version}"
    PLUGIN_PATH = OUTPUT_DIR / plugin_name
    PLUGIN_TORCH_DST = PLUGIN_PATH / "_internal"

    PLUGIN_TORCH_DST.mkdir(parents=True, exist_ok=True)

    for src_folder in DIST_INTERNAL_PATH.glob("torch*"):
        print(f" - {str(src_folder.name)}")
        dst_folder = PLUGIN_TORCH_DST / src_folder.name
        shutil.rmtree(dst_folder, ignore_errors=True)
        shutil.copytree(src_folder, dst_folder)

    print(f"\n🗜️ Creating CUDA plugin archive")
    # Makes too big archive (2.1GB), GitHub limit is 2GB
    # PLUGIN_ZIP = OUTPUT_DIR / f"{plugin_name}.zip"
    # shutil.make_archive(base_name=PLUGIN_ZIP.with_suffix(''), format='zip', root_dir=PLUGIN_PATH)
    # make_zip_with_max_compression(zip_path=PLUGIN_ZIP, source_dir=PLUGIN_PATH)

    # Makes perfect ~1.3 GB archive
    PLUGIN_7Z = OUTPUT_DIR / f"{plugin_name}.7z"
    PLUGIN_INTERNAL = PLUGIN_PATH / "_internal"

    with py7zr.SevenZipFile(PLUGIN_7Z, 'w',
            filters=[{"id": py7zr.FILTER_LZMA2, "preset": 9}]) as archive:
        write_with_progress(archive, PLUGIN_INTERNAL, "_internal")

    size_mb = PLUGIN_7Z.stat().st_size / (1024 * 1024)
    print(f"✅ Success! {PLUGIN_7Z.name} ({size_mb:.1f} MB) ready.")



def create_zip(version: str):
    print(f"\n🚫 Deleting Torch subfolders")
    for src_folder in DIST_INTERNAL_PATH.glob("torch*"):
        print(f" - {str(src_folder.name)}")
        shutil.rmtree(src_folder, ignore_errors=True)

    ZIP_PATH = OUTPUT_DIR / f"{APP_NAME}-{version}-Win64-Portable.zip"
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print(f"\n🗜️ Creating ZIP archive")
    # shutil.make_archive(base_name=ZIP_PATH.with_suffix(''), format='zip', root_dir=DIST_PATH)
    make_zip_with_max_compression(zip_path=ZIP_PATH, source_dir=DIST_PATH)

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"✅ Success! {ZIP_PATH.name} ({size_mb:.1f} MB) ready.")



def create_installer(OUTPUT_EXE: Path, version: str, full_version: str, en: dict, ru: dict):
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
    else:
        print("❌ Output EXE not found.", file=sys.stderr)
        sys.exit(1)



def generate_winget_manifest(version: str, OUTPUT_EXE: Path, en: dict, ru: dict):
    installer_url = f"https://github.com/{GITHUB_REPO}/releases/download/{version}/{OUTPUT_EXE.name}"
    installer_hash = calculate_sha256(OUTPUT_EXE)
    
    version_manifest = f"""# Created using wingetcreate 1.10.3.0
# yaml-language-server: $schema=https://aka.ms/winget-manifest.version.1.10.0.schema.json

PackageIdentifier: {PRODUCER_NAME}.{APP_NAME}
PackageVersion: {version}
DefaultLocale: en-US
ManifestType: version
ManifestVersion: 1.10.0
"""
    
    installer_manifest = f"""# Created using wingetcreate 1.10.3.0
# yaml-language-server: $schema=https://aka.ms/winget-manifest.installer.1.10.0.schema.json

PackageIdentifier: {PRODUCER_NAME}.{APP_NAME}
PackageVersion: {version}
InstallerType: nullsoft
Installers:
- Architecture: x64
  InstallerUrl: {installer_url}
  InstallerSha256: {installer_hash}
ManifestType: installer
ManifestVersion: 1.10.0
"""

    locale_en_manifest = f"""# Created using wingetcreate 1.10.3.0
# yaml-language-server: $schema=https://aka.ms/winget-manifest.defaultLocale.1.10.0.schema.json

PackageIdentifier: {PRODUCER_NAME}.{APP_NAME}
PackageVersion: {version}
PackageLocale: en-US
Publisher: {PRODUCER_NAME}
PublisherUrl: https://github.com/DeXP
PublisherSupportUrl: https://github.com/{GITHUB_REPO}/issues
Author: DeXP
PackageName: EbookTalker
PackageUrl: https://github.com/{GITHUB_REPO}
License: {LICENSE}
LicenseUrl: https://github.com/{GITHUB_REPO}/blob/main/LICENSE.md
Copyright: {en["LegalCopyright"]}
ShortDescription: {en["appDescription"]}
Moniker: {APP_NAME.lower()}
Tags:
- ebook
- tts
- reader
- accessibility
- open-source
ReleaseNotes: See release notes on GitHub - https://github.com/{GITHUB_REPO}/releases/tag/{version}
ReleaseNotesUrl: https://github.com/{GITHUB_REPO}/releases/tag/{version}
ManifestType: defaultLocale
ManifestVersion: 1.10.0
"""
    
    locale_ru_manifest = f"""# yaml-language-server: $schema=https://aka.ms/winget-manifest.locale.1.10.0.schema.json

PackageIdentifier: {PRODUCER_NAME}.{APP_NAME}
PackageVersion: {version}
PackageLocale: ru-RU
Publisher: {PRODUCER_NAME}
Copyright: {ru["LegalCopyright"]}
ShortDescription: {ru["appDescription"]}
ReleaseNotes: Смотрите изменения на GitHub - https://github.com/{GITHUB_REPO}/releases/tag/{version}
ReleaseNotesUrl: https://github.com/{GITHUB_REPO}/releases/tag/{version}
ManifestType: locale
ManifestVersion: 1.10.0
"""

    manifest_folder = OUTPUT_DIR / "winget-pkgs" / "manifests" / f"{PRODUCER_NAME[0].lower()}" / PRODUCER_NAME / APP_NAME / version
    manifest_folder.mkdir(parents=True, exist_ok=True)

    version_manifest_path = manifest_folder / f"{PRODUCER_NAME}.{APP_NAME}.yaml"
    version_manifest_path.write_text(version_manifest, encoding="utf-8")

    installer_manifest_path = manifest_folder / f"{PRODUCER_NAME}.{APP_NAME}.installer.yaml"
    installer_manifest_path.write_text(installer_manifest, encoding="utf-8")

    locale_en_manifest_path = manifest_folder / f"{PRODUCER_NAME}.{APP_NAME}.locale.en-US.yaml"
    locale_en_manifest_path.write_text(locale_en_manifest, encoding="utf-8")

    locale_ru_manifest_path = manifest_folder / f"{PRODUCER_NAME}.{APP_NAME}.locale.ru-RU.yaml"
    locale_ru_manifest_path.write_text(locale_ru_manifest, encoding="utf-8")

    print(f"\n📝 Generated winget manifest: {manifest_folder}")


# === Main build logic ===
def main():
    print(f"📖 {APP_NAME} Installer creator script")
    en = json.loads(EN_PATH.read_text(encoding='utf8'))
    ru = json.loads(RU_PATH.read_text(encoding='utf8'))

    version = VERSION_FILE_PATH.read_text().strip()
    full_version = version
    while full_version.count('.') < 3:
        full_version += '.0'

    OUTPUT_EXE = OUTPUT_DIR / f"{APP_NAME}-{version}-Win64-Installer.exe"


    if (len(sys.argv) < 2) or ('all' == sys.argv[1]):
        # Default - do all
        create_exe(en, ru, version, full_version)
        create_zip(version)
        create_installer(OUTPUT_EXE, version, full_version, en, ru)
        generate_winget_manifest(version, OUTPUT_EXE, en, ru)
    else:
        for i in range(1, len(sys.argv)):
            mode = str(sys.argv[i]).lower()
            if ('exe' == mode):
                create_exe(en, ru, version, full_version)
            elif ('cuda' == mode):
                extract_cuda()
            elif ('zip' == mode):
                create_zip(version)
            elif ('installer' == mode):
                create_installer(OUTPUT_EXE, version, full_version, en, ru)
            elif ('manifest' == mode):
                generate_winget_manifest(version, OUTPUT_EXE, en, ru)
            elif ('-h' == mode) or ('/?' == mode) or ('h' == mode) or ('help' == mode) or ('--help' == mode):
                print(f"""
Call the script without arguments, so all artifacts (except cuda) would be created. Or provide one or multiple of the following:
  help - Show this help
  exe - Pack python files to executable with PyInstaller
  cuda - Extract CUDA DLLs from executable and pack it as a plugin
  zip - Archive Portable-version of the app
  installer - Make a Nullsoft installer
  manifest - Generate manifest to submit to WinGet

Example:
                      
{sys.argv[0]} installer manifest
- this command will not invoke PyInstaller or zip-archiver. Might be useful for installer tweaking.

{sys.argv[0]} exe cuda
- generate CUDA plugin 7z archive - you usually need it just one per Torch/Cuda version
""")



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
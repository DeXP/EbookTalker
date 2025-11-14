# core/downloader.py
import os, sys, shutil, tempfile, threading, ctypes, hashlib, requests, queue
from pathlib import Path
from typing import Optional

from .DownloadItem import DownloadItem
from .detection import is_process_elevated


# Elevate robocopy directly (Windows-only)
def elevate_robocopy(src: Path, dest: Path) -> bool:
    if sys.platform != "win32":
        return False

    # Prepare robocopy args
    # /E = copy subdirs, /MOVE = delete source after - bad, /COPYALL — copy all file info, /Z = resumeable, /R:1 /W:1 = fast retry
    args = f'"{src}" "{dest}" /E /COPYALL /Z /R:1 /W:1'

    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    SW_HIDE = 0

    class SHELLEXECUTEINFOW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("fMask", ctypes.c_ulong),
            ("hwnd", ctypes.c_void_p),
            ("lpVerb", ctypes.c_wchar_p),
            ("lpFile", ctypes.c_wchar_p),
            ("lpParameters", ctypes.c_wchar_p),
            ("lpDirectory", ctypes.c_wchar_p),
            ("nShow", ctypes.c_int),
            ("hInstApp", ctypes.c_void_p),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", ctypes.c_wchar_p),
            ("hKeyClass", ctypes.c_void_p),
            ("dwHotKey", ctypes.c_ulong),
            ("hIcon", ctypes.c_void_p),
            ("hProcess", ctypes.c_void_p)
        ]

    sei = SHELLEXECUTEINFOW()
    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFOW)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS
    sei.lpVerb = "runas"
    sei.lpFile = "robocopy.exe"
    sei.lpParameters = args
    sei.nShow = SW_HIDE

    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei)):
        return False

    if sei.hProcess:
        ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 0xFFFFFFFF)
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)

    return True


class DownloaderCore:
    def __init__(self, item: DownloadItem, cancel_event: threading.Event, status_queue: queue.Queue):
        self.item = item
        self.cancel_event = cancel_event
        self.status_queue = status_queue
        self.temp_file = None
        self.extracted_dir = None

    def _send_status(self, msg: str):
        self.status_queue.put(("message", msg))

    def _send_progress(self, stage: str, percent: float):
        self.status_queue.put(("progress", percent))

    def _send_indeterminate(self, enable: bool):
        self.status_queue.put(("indeterminate", enable))

    def run(self) -> bool:
        try:
            item = self.item
            self._send_status("Processing")

            # 1. Download
            self._send_status("Downloading...")
            self.temp_file = self._download_with_progress(item.url, item.sha256)
            if not self.temp_file:
                return False

            if self.cancel_event.is_set():
                self._send_status("Installation canceled during download.")
                return False

            # 2. Extract or prepare
            if item.is_archive:
                self._send_indeterminate(True)
                self._send_status("Extracting...")
                self.extracted_dir = Path(tempfile.mkdtemp())
                if not self._extract_7z(self.temp_file, self.extracted_dir):
                    self._send_indeterminate(False)
                    return False
                source_path = self.extracted_dir
            else:
                filename = Path(item.url).name
                final_temp = self.extracted_dir = Path(tempfile.mkdtemp()) / filename
                shutil.move(self.temp_file, final_temp)
                self.temp_file = None
                source_path = final_temp

            # 3. Copy
            self._send_status("Copying files...")
            success = self._copy_with_elevation_if_needed(source_path, item)
            self._send_indeterminate(False)
            if not success:
                return False

            self._send_status(f"Installed")
            return True

        except Exception as e:
            self._send_indeterminate(False)
            self._send_status(f"Error: {e}")
            return False
        finally:
            self._cleanup()

    def _cleanup(self):
        if self.temp_file and os.path.exists(self.temp_file):
            try: os.unlink(self.temp_file)
            except: pass
        if self.extracted_dir and self.extracted_dir.exists():
            try: shutil.rmtree(self.extracted_dir, ignore_errors=True)
            except: pass

    def _download_with_progress(self, url: str, expected_sha256: Optional[str]) -> Optional[str]:
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            try:
                with requests.get(url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    total = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    hasher = hashlib.sha256()
                    with open(tmp_path, 'wb') as f:
                        for chunk in r.iter_content(16384):
                            if self.cancel_event.is_set():
                                raise KeyboardInterrupt()
                            f.write(chunk)
                            hasher.update(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                self._send_progress("download", downloaded / total * 100)
                if expected_sha256 and hasher.hexdigest().lower() != expected_sha256.lower():
                    self._send_status("Checksum mismatch!")
                    return None
                if expected_sha256:
                    self._send_status("Checksum OK.")
                return tmp_path
            except Exception as e:
                self._send_status(f"Download failed: {e}")
                return None
        except KeyboardInterrupt:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try: os.unlink(tmp_path)
                except: pass
            return None

    def _extract_7z(self, archive_path: str, dest_dir: Path) -> bool:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            import py7zr
            with py7zr.SevenZipFile(archive_path, 'r') as z:
                z.extractall(path=str(dest_dir))
            return True
        except:
            return False

    def _copy_with_elevation_if_needed(self, src: Path, item: DownloadItem) -> bool:
        dest = item.dest 
        if sys.platform == "win32" and not is_process_elevated():
            prog_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
            needs_elev = item.needs_admin or (prog_files.resolve() in dest.resolve().parents)
        else:
            needs_elev = False

        if not needs_elev:
            try:
                if src.is_dir():
                    # if dest.exists():
                    #     shutil.rmtree(dest, ignore_errors=True)
                    shutil.copytree(src, dest)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                return True
            except Exception as e:
                self._send_status(f"Local copy failed: {e}")
                return False

        return elevate_robocopy(src, dest)

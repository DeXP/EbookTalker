import os, shutil
from pathlib import Path

from . import dxtmpfile


def MoveFile(tmpFolder: Path, fromFile: Path, toFile: Path):
    if dxtmpfile.IsPythonNative():
        if fromFile.exists() and (not toFile.exists()):
            # fromFile.rename(toFile) # - don't work on different FS. Example: mounted docker folder
            shutil.move(fromFile.absolute(), toFile.absolute())
    else:
        with dxtmpfile.TmpNameFile(tmpFolder, fromFile) as fromNameFile:
            with dxtmpfile.TmpNameFile(tmpFolder, toFile) as toNameFile:
                cmd = f"mv {fromNameFile} {toNameFile}"
                os.system(cmd)


def MoveAllFiles(tmpFolder: Path, fromFolder: Path, toFolder: Path):
    if fromFolder.exists():
        for file in fromFolder.iterdir():
            if file.is_file():
                MoveFile(tmpFolder, file, toFolder / file.name)


def CreateDirectory(tmpFolder: Path, folder: Path):
    if dxtmpfile.IsPythonNative():
        folder.mkdir(parents=True, exist_ok=True)
    else:
        with dxtmpfile.TmpNameFile(tmpFolder, folder) as dirNameFile:
            cmd = f"mkdir -p {dirNameFile}"
            os.system(cmd)


def RemoveDirectoryRecursively(pth: Path):
    for child in pth.iterdir():
        if child.is_file():
            child.unlink()
        else:
            RemoveDirectoryRecursively(child)
    try:
        pth.rmdir()
    except:
        pass

import os
from pathlib import Path

from . import dxtmpfile


def SafeFileName(origName):
    keepcharacters = (' ','.','!','-','_')
    return "".join(c for c in origName if c.isalnum() or c in keepcharacters).rstrip()


def MoveFile(tmpFolder: Path, fromFile: Path, toFile: Path):
    if dxtmpfile.IsPythonNative():
        if not toFile.exists():
            fromFile.rename(toFile)
    else:
        with dxtmpfile.TmpNameFile(tmpFolder, fromFile) as fromNameFile:
            with dxtmpfile.TmpNameFile(tmpFolder, toFile) as toNameFile:
                cmd = f"mv {fromNameFile} {toNameFile}"
                os.system(cmd)


def MoveAllFiles(tmpFolder: Path, fromFolder: Path, toFolder: Path):
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
    pth.rmdir()
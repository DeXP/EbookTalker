import sys, uuid
from pathlib import Path

class TmpStringFile:
    def __init__(self, tmpFolder: Path, stringContent, ext='.string'):
        self.file = tmpFolder / f'{uuid.uuid4()}{ext}'
        self.content = stringContent.encode(encoding="utf-8")

    def __enter__(self):
        self.file.write_bytes(self.content)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.unlink()
        return True

    def Path(self):
        return self.file.absolute()
    
    def UnQuotedCat(self):
        return f"`cat {self.Path()}`"
    
    def QuotedCat(self):
        return f"\"{self.UnQuotedCat()}\""
    
    def __str__(self):
     return self.QuotedCat()

    
class TmpNameFile(TmpStringFile):
    def __init__(self, tmpFolder: Path, nameContent: Path):
        nameString = str(nameContent.absolute())
        TmpStringFile.__init__(self, tmpFolder, nameString, ext='.name')


def Encoding():
    return sys.getfilesystemencoding()


def IsPythonNative():
    return 'utf-8' == sys.getfilesystemencoding()
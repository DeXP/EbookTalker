import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


def SafeFileName(origName):
    keepcharacters = (' ','.','!','-','_')
    return "".join(c for c in origName if c.isalnum() or c in keepcharacters).rstrip()


def AuthorName(info: dict):
    if not info:
        return None
    if 'author' in info:
        return str(info['author']).strip()
    isRussian = ('lang' in info) and ('ru' == info['lang'])
    first = (" " + info['firstName']) if ('firstName' in info) and info['firstName'] else ""
    middle = (" " + info['middleName']) if (not isRussian) and ('middleName' in info) and info['middleName'] else ""
    last = (" " + info['lastName']) if ('lastName' in info) and info['lastName'] else ""
    return (first + middle + last).strip()


def SafeAuthorName(info: dict):
    return SafeFileName(AuthorName(info))


def BookName(info, includeAuthor = True):
    if not info:
        return None
    author = AuthorName(info) if includeAuthor else ""
    num = (" " + info['seqNumber']) if ('seqNumber' in info) and info['seqNumber'] else ""
    title = (" " + info['title']) if ('title' in info) and info['title'] else ""
    if includeAuthor and author:
        return (author + " -" + num + title).strip()
    else:
        return (num + title).strip()
    

def SafeBookName(info, includeAuthor = True):
    return SafeFileName(BookName(info, includeAuthor=includeAuthor))
    

def GetFileBytes(input: Path):
    try:
        file_path = input.absolute()
        isZip = False
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            isZip = (magic == b'PK\x03\x04')  # ZIP file magic number

        if not isZip:
            return input.read_bytes()
        else:
            with zipfile.ZipFile(file_path) as zip_file:
                for file_info in zip_file.infolist():
                    if not file_info.is_dir():
                        with zip_file.open(file_info) as file_in_zip:
                            return file_in_zip.read()
                return None  # ZIP contained no file
    except (zipfile.BadZipFile, PermissionError, IOError):
        return None


def ParseBook(file: Path, full = False):
    from helpers import fb2, epub, txt
    
    ext = file.suffix.lower()
    if '.epub' == ext:
        return epub.ParseEpub(file, full)
    elif '.txt' == ext:
        return txt.ParseTXT(file, full)
    else:
        return fb2.ParseFB2(file, full)
    


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Coverts FB2/EPUB/TXT book to JSON')
    parser.add_argument('-i', '--input', help='Input file')

    args = parser.parse_args()

    if not args.input:
        print("Please provide input file")
    else:
        input = Path(args.input)
        isFull = True
        info, _ = ParseBook(input, full=isFull)
        print(info)
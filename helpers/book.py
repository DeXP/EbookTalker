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


def SafeBookFileName(info, includeAuthor = True):
    ext = info['ext'] if ('ext' in info) else 'tmp'
    return SafeFileName(BookName(info, includeAuthor=includeAuthor)) + "." + ext


def GetTestBook(tr: dict):
    return {
            'error': '',
            'ext': 'epub',
            'author': tr["author"],
            'firstName': tr["firstName"],
            'middleName': '',
            'lastName': tr['lastName'],
            'title': tr['title'],
            'lang': 'en',
            'sequence': tr["sequence"],
            'seqNumber': '',
            'cover': 'BookCover.jpg',
            'encoding': 'utf-8',
            'file': 'file.name',
            'size': 123456,
            'datetime': 0.0,
        }


def GetOutputName(outputDir: Path, info: dict, dirFormat: str) -> Path:
    lowerFormat = dirFormat.lower()
    if ("full" == lowerFormat) or ("short" == lowerFormat):
        # Full format - create sub folders
        author = SafeAuthorName(info)
        bookName = SafeBookName(info, includeAuthor=False)
        if ("full" == lowerFormat) and ('sequence' in info) and info['sequence']:
            return outputDir / author / SafeFileName(info['sequence']) / bookName
        else:
            return outputDir / author / bookName
    else:
        # Single - all books into same folder
        return outputDir / SafeBookName(info, includeAuthor=True)


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


def DetermineBookFileType(file_path):
    # First check if it's a ZIP archive (FB2.ZIP or TXT.ZIP)
    if is_zip_file(file_path):
        # Check for EPUB first as it's the most specific ZIP-based format
        if is_epub(file_path):
            return "epub"
        # Then check if it contains an FB2 file
        if contains_fb2(file_path):
            return "fb2.zip"
        # Otherwise assume it's a text file in ZIP
        return "txt.zip"
    
    # Check for raw FB2 (not in ZIP)
    if is_fb2(file_path):
        return "fb2"
    
    # If none of the above, assume it's plain text
    return "txt"


def is_zip_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return f.read(4) == b'PK\x03\x04'
    except:
        return False


def contains_fb2(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for name in z.namelist():
                if name.lower().endswith('.fb2'):
                    return True
                # Check if any file starts with FB2 signature
                with z.open(name) as f:
                    if f.read(50).decode('utf-8', errors='ignore').lstrip().startswith('<'):
                        return True
            return False
    except:
        return False

def is_epub(file_path):
    try:
        # EPUB is a ZIP file that contains mimetype file with exact content
        if not is_zip_file(file_path):
            return False
            
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'mimetype' not in z.namelist():
                return False
            with z.open('mimetype') as f:
                mimetype = f.read(30).decode('ascii', errors='ignore')
                return mimetype.startswith('application/epub+zip')
    except:
        return False

def is_fb2(file_path):
    try:
        with open(file_path, 'rb') as f:
            # FB2 files start with XML declaration or directly with <FictionBook
            start = f.read(200).decode('utf-8', errors='ignore').lstrip()
            if start.startswith('\ufeff'):
                start = start[1:]
            return start.startswith(('<?xml', '<FictionBook'))
    except:
        return False
    

def ParseBook(file: Path, full = False):
    from helpers import fb2, epub, txt
    fileType = DetermineBookFileType(str(file.absolute()))
    if 'epub' == fileType:
        return epub.ParseEpub(file, full)
    elif fileType.startswith('fb2'): # FB2 and FB2.zip
        return fb2.ParseFB2(file, full)
    else:
        return txt.ParseTXT(file, full)
    


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Coverts FB2/EPUB/TXT book to JSON')
    parser.add_argument('-i', '--input', help='Input file')

    args = parser.parse_args()

    if not args.input:
        print("Please provide input file")
    else:
        input = Path(args.input)
        fileType = DetermineBookFileType(args.input)
        print(fileType)
        isFull = True
        info, _ = ParseBook(input, full=isFull)
        print(info)
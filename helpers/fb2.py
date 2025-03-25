import re, io, base64, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    import dxnormalizer, dxsplitter
else:
    from helpers import dxnormalizer, dxsplitter


def AuthorName(info: dict):
    if not info:
        return None
    isRussian = ('lang' in info) and ('ru' == info['lang'])
    first = (" " + info['firstName']) if ('firstName' in info) and info['firstName'] else ""
    middle = (" " + info['middleName']) if (not isRussian) and ('middleName' in info) and info['middleName'] else ""
    last = (" " + info['lastName']) if ('lastName' in info) and info['lastName'] else ""
    return (first + middle + last).strip()


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
    

def getElem(el: ET.Element, name):
    return el.find(name) if (el is not None) else None


def getAttrib(el: ET.Element, name):
    return el.attrib[name] if (el is not None) and (name in el.attrib) else None


def getAttribByEnd(el: ET.Element, name):
    if (el is None) or (el.attrib is None):
        return None
    for k in el.attrib.keys():
        if k.endswith(name):
            return el.attrib[k]
    return None

def getText(el: ET.Element, name):
    textTag = el.find(name) if (el is not None) else None
    return textTag.text if (textTag is not None) else None


def getElText(el: ET.Element):
    return el.text if (el is not None) else None


def getSectionTitle(section: ET.Element):
    sectionTitle = getElem(section, 'title')
    sectionTitleText = ''
    if sectionTitle is not None:
        for st in sectionTitle.itertext():
            ct = st.strip()
            if ct:
                if sectionTitleText:
                    sectionTitleText += ". "
                sectionTitleText += ct
    if (sectionTitleText):
        sectionTitleText += '.'
    return sectionTitleText


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


def ParseFB2(file: Path, full = False):
    rawdata = GetFileBytes(file)
    if not rawdata:
        return {'error': 'file-access', 'failure': f"Cannot read {file}"}, None
    first_line = rawdata[:80].decode('utf-8')
    encoding = ''
    match = re.search(' encoding="[^"]+"', first_line)
    if match:
        encoding = match.group(0)[11:-1]

    origxmlstring = ''
    try:
        origxmlstring = rawdata.decode(encoding=encoding)
    except:
        return {'error': 'charset-decoding', 'failure': encoding}, None
    xmlstring = re.sub(' xmlns="[^"]+"', '', origxmlstring, count=1) # cut namespace
    
    try:
        root = ET.fromstring(xmlstring)

        descriptionTag = root.find('description')
        titleInfo = getElem(descriptionTag, 'title-info')
        sequence = getElem(titleInfo, 'sequence')
        author = getElem(titleInfo, 'author')
        lang = getText(titleInfo, 'lang')

        coverBytes = None
        coverPage = getElem(titleInfo, 'coverpage')
        coverImage = getElem(coverPage, 'image')
        coverName = getAttribByEnd(coverImage, 'href')
        if coverName and coverName.startswith('#'):
            coverName = coverName[1:]

            for binary in root.findall('binary'):
                if coverName == getAttrib(binary, 'id'):
                    coverBytes = base64.b64decode(binary.text)    
        
        sections = []
        if full:
            body = root.find('body')
            for section in body.findall('section'):
                p = []
                rawSectionTitle = getSectionTitle(section)
                sectionTitle = dxnormalizer.normalize(rawSectionTitle, lang)

                for subTag in section:
                    if 'title' == subTag.tag:
                        continue

                    curText = ''
                    for t in subTag.itertext():
                        curText += t

                    # tts = curText
                    tts = dxnormalizer.normalize(curText, lang)
                    
                    # if 'ru' == info['lang']:
                    #     out_text = predictor.stress_text(var['accent_ru'], tts)
                    #     tts = ''.join(out_text)

                    #splitter = SentenceSplitter(language=info['lang'])
                    #sentences = splitter.split(tts)
                    sentences = dxsplitter.SplitSentence(tts)

                    p.append(sentences) # Add as 2D list

                sections.append({
                    'title': sectionTitle,
                    'text': p
                })
                

        return {
            'error': '',
            'firstName': getText(author, 'first-name'),
            'middleName': getText(author, 'middle-name'),
            'lastName': getText(author, 'last-name'),
            'title': getText(titleInfo, 'book-title'),
            'lang': lang,
            'sequence': getAttrib(sequence, 'name'),
            'seqNumber': getAttrib(sequence, 'number'),
            'cover': coverName,
            'encoding': encoding,
            'file': file.name,
            'size': file.stat().st_size,
            'datetime': file.lstat().st_mtime,
            # Data, available in a full parse only
            'sections': sections
        }, root
    except Exception as error:
        return {'error': 'book-format', 'failure': str(error)}, None


def ParseTXT(file: Path, full = False):
    import chardet
    encoding = 'utf8'
    rawText = ''
    rawData = GetFileBytes(file)
    if not rawData:
        return {'error': 'file-access', 'failure': f"Cannot read {file}"}
    encoding = chardet.detect(rawData)['encoding']
    try:
        rawText = rawData.decode(encoding=encoding)
    except Exception as error:
        return {'error': 'book-format', 'failure': str(error)}

    title = file.stem
    name = ''
    middle = ''
    surname = ''
    pattern = r'^(.+?) (.+?) - (.+?)$'
    match = re.fullmatch(pattern, file.stem)
    if match:
        name = match.group(1)
        surname = match.group(2)
        title = match.group(3)
    else:
        pattern = r'^(.+?) (.+?) (.+?) - (.+?)$'
        match = re.fullmatch(pattern, file.stem)
        if match:
            name = match.group(1)
            middle = match.group(2)
            surname = match.group(3)
            title = match.group(4)

    lang = dxnormalizer.detect_language(rawText)
    p = []
    if full:
        for line in rawText.split('\n'):
            if line.strip():
                tts = dxnormalizer.normalize(line, lang)
                p.append(dxsplitter.SplitSentence(tts))
    return {
        'error': '',
        'firstName': name,
        'middleName': middle,
        'lastName': surname,
        'title': title,
        'lang': lang,
        'sequence': '',
        'seqNumber': '',
        'cover': '',
        'encoding': encoding,
        'file': file.name,
        'size': file.stat().st_size,
        'datetime': file.lstat().st_mtime,
        # Data, available in a full parse only
        'sections': [{
            'title': title,
            'text': p
        }]  
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Coverts FB2/TXT book to JSON')
    parser.add_argument('-i', '--input', help='Input file')

    args = parser.parse_args()

    if not args.input:
        print("Please provide input file")
    else:
        input = Path(args.input)
        isFull = True
        ext = input.suffix.lower()
        if ext == '.txt':
            info = ParseTXT(input, full=isFull)
        else:
            info, root = ParseFB2(input, full=isFull)
        print(info)
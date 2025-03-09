import re
from pathlib import Path
import xml.etree.ElementTree as ET


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


def ParseFB2(file: Path):
    encoding = ''
    with open(file.absolute(), 'rb') as f:
        first_line = f.read(80).decode('utf-8')
        match = re.search(' encoding="[^"]+"', first_line)
        if match:
            encoding = match.group(0)[11:-1]

    origxmlstring = ''
    try:
        #origxmlstring = file.read_text(encoding=encoding)
        rawdata = open(file.absolute(), "rb").read()
        origxmlstring = rawdata.decode(encoding=encoding)
    except:
        return {'error': 'file-access', 'failure': encoding}, None
    xmlstring = re.sub(' xmlns="[^"]+"', '', origxmlstring, count=1) # cut namespace
    
    try:
        root = ET.fromstring(xmlstring)

        descriptionTag = root.find('description')
        titleInfo = getElem(descriptionTag, 'title-info')
        sequence = getElem(titleInfo, 'sequence')
        author = getElem(titleInfo, 'author')

        coverPage = getElem(titleInfo, 'coverpage')
        coverImage = getElem(coverPage, 'image')
        coverName = getAttribByEnd(coverImage, 'href')
        if coverName and coverName.startswith('#'):
            coverName = coverName[1:]

        return {
            'firstName': getText(author, 'first-name'),
            'middleName': getText(author, 'middle-name'),
            'lastName': getText(author, 'last-name'),
            'title': getText(titleInfo, 'book-title'),
            'lang': getText(titleInfo, 'lang'),
            'sequence': getAttrib(sequence, 'name'),
            'seqNumber': getAttrib(sequence, 'number'),
            'cover': coverName,
            'encoding': encoding,
            'file': file.name,
            'size': file.stat().st_size,
            'datetime': file.lstat().st_mtime,
            'error': ''
        }, root
    except Exception as error:
        return {'error': 'fb2-format', 'failure': str(error)}, None
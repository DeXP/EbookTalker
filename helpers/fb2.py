import re, base64
from pathlib import Path
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    import book, dxnormalizer, dxsplitter
else:
    from . import book, dxnormalizer, dxsplitter


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


def ParseFB2(file: Path, full = False):
    rawdata = book.GetFileBytes(file)
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
        lang = dxnormalizer.unify_lang(getText(titleInfo, 'lang'))

        coverBytes = None
        coverPage = getElem(titleInfo, 'coverpage')
        coverImage = getElem(coverPage, 'image')
        coverName = getAttribByEnd(coverImage, 'href')
        if coverName and coverName.startswith('#'):
            coverName = coverName[1:]
            if full:
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
            'ext': 'fb2',
            'firstName': getText(author, 'first-name'),
            'middleName': getText(author, 'middle-name'),
            'lastName': getText(author, 'last-name'),
            'title': getText(titleInfo, 'book-title'),
            'lang': lang,
            'sequence': getAttrib(sequence, 'name'),
            'seqNumber': getAttrib(sequence, 'number'),
            'cover': coverName,
            'encoding': encoding,
            'size': file.stat().st_size,
            'datetime': file.lstat().st_mtime,
            # Data, available in a full parse only
            'sections': sections
        }, coverBytes
    except Exception as error:
        return {'error': 'book-format', 'failure': str(error)}, None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Coverts FB2 book to JSON')
    parser.add_argument('-i', '--input', help='Input file')

    args = parser.parse_args()

    if not args.input:
        print("Please provide input file")
    else:
        input = Path(args.input)
        isFull = True
        info, _ = ParseFB2(input, full=isFull)
        print(info)
import re
from pathlib import Path

if __name__ == "__main__":
    import book, dxnormalizer, dxsplitter
else:
    from . import book, dxnormalizer, dxsplitter


def ParseTXT(file: Path, full = False):
    import chardet
    encoding = 'utf8'
    rawText = ''
    rawData = book.GetFileBytes(file)
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
        'ext': 'txt',
        'suggestedFileName': file.name,
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
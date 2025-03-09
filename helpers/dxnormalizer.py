import re
from transliterate import translit
from num2words import num2words

russian_chars = re.compile('[а-яА-ЯёЁ]')


def is_russian(text):
    return True if re.search(russian_chars, text) else False       


def detect_language(text, lang = 'ru') -> str:
    if (not text):
        return lang
    ukraine_chars = re.compile('[ґєї]')
    english_chars = re.compile('[a-zA-Z]')

    if re.search(ukraine_chars, text):
        return 'uk'
    elif re.search(russian_chars, text):
        return 'ru'
    elif re.search(english_chars, text):
        return 'en' 
    else:
        return lang
    

def normalize_number(text: str, lang = 'ru') -> str:
    def replacer(match):
        return num2words(int(match.group()), lang=lang)
    
    return re.sub(r'\d+', replacer, text)


def translit_text(text: str, lang = 'ru') -> str:
    english_words = re.findall(r'[a-zA-Z]+', text)

    for word in english_words:
        result = translit(word, lang)
        text = text.replace(word, result)

    return text


def normalize(text: str, lang = 'ru') -> str:
    # text = " ".join(text.split())
    text = normalize_number(text, lang)
    text = translit_text(text, lang)

    return text
import re
#from transliterate import translit
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



def transliterate_to_russian(text):
    # Define phonetic patterns for transliteration
    patterns = {
        # Single letters
        'a': 'а', 'b': 'б', 'c': 'к', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
        'h': 'х', 'i': 'и', 'j': 'дж', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
        'o': 'о', 'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у',
        'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'й', 'z': 'з',
        # Common digraphs and trigraphs
        'ch': 'ч', 'sh': 'ш', 'zh': 'ж', 'th': 'з', 'ph': 'ф', 'kh': 'х',
        'ts': 'ц', 'ya': 'я', 'ye': 'е', 'yo': 'ё', 'yu': 'ю', 'yi': 'и',
        'ai': 'ай', 'ei': 'эй', 'oi': 'ой', 'ui': 'уй', 'au': 'ау', 'ou': 'оу',
        'ia': 'ия', 'ie': 'ие', 'io': 'ио', 'iu': 'иу', 'ua': 'уа', 'ue': 'уе',
        'uo': 'уо', 'uu': 'уу',
        # Special cases
        'ough': 'уу',  # e.g., "through" → "сруу"
        'tion': 'шн',  # e.g., "nation" → "нэйшн"
        'sion': 'жн',  # e.g., "vision" → "вижн"
        'ation': 'эйшн',  # e.g., "liberation" → "либерацйон"
        'by': 'бай',  # e.g., "by" → "бай"
        'and': 'энд',  # e.g., "and" → "энд"
        'ght': 'т',  # e.g., "light" → "лайт", "tight" → "тайт"
        'ow': 'оу',  # e.g., "rainbow" → "райнбоу"
        'circular': 'циркулар',  # e.g., "circular" → "циркулар"
    }

    # Function to transliterate a single word while preserving case
    def transliterate_word(word):
        # Check if the word is uppercase, lowercase, or capitalized
        if word.isupper():
            case = 'upper'
        elif word.istitle():
            case = 'title'
        else:
            case = 'lower'

        # Convert the word to lowercase for processing
        word_lower = word.lower()

        # Replace specific patterns first (longer patterns first)
        for pattern, replacement in sorted(patterns.items(), key=lambda x: -len(x[0])):
            word_lower = word_lower.replace(pattern, replacement)

        # Handle "y" at the end of the word
        if word_lower.endswith('y'):
            # If the word ends with "y," check if it's a single-syllable word
            # (e.g., "sky," "fly") or part of a longer word (e.g., "commonly," "usually")
            syllable_count = sum(1 for char in word_lower if char in 'aeiouy')
            if syllable_count <= 2:  # Single-syllable or short words
                word_lower = word_lower[:-1] + 'ай'
            else:  # Longer words
                word_lower = word_lower[:-1] + 'и'

        # Handle remaining characters
        result = []
        i = 0
        while i < len(word_lower):
            # Check for multi-character patterns
            matched = False
            for length in range(4, 0, -1):  # Check patterns of length 4, 3, 2, 1
                if i + length <= len(word_lower) and word_lower[i:i+length] in patterns:
                    result.append(patterns[word_lower[i:i+length]])
                    i += length
                    matched = True
                    break
            if not matched:
                # If no pattern matches, keep the original character
                result.append(word_lower[i])
                i += 1

        # Restore the original case
        transliterated_word = ''.join(result)
        if case == 'upper':
            return transliterated_word.upper()
        elif case == 'title':
            return transliterated_word.title()
        else:
            return transliterated_word

    # Split the text into words and transliterate each word
    words = text.split(' ')
    transliterated_words = [transliterate_word(word) for word in words]
    return ' '.join(transliterated_words)



def normalize_number(text: str, lang = 'ru') -> str:
    def replacer(match):
        return num2words(int(match.group()), lang=lang)
    
    return re.sub(r'\d+', replacer, text)


def translit_text(text: str, lang = 'ru') -> str:
    english_words = re.findall(r'[a-zA-Z]+', text)

    for word in english_words:
        # result = translit(word, lang)
        result = transliterate_to_russian(word) if ('ru' == lang) else word
        text = text.replace(word, result)

    return text


def normalize(text: str, lang = 'ru') -> str:
    # text = " ".join(text.split())
    text = normalize_number(text, lang)
    text = translit_text(text, lang)

    return text
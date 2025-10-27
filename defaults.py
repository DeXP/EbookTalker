from pathlib import Path

def GetDefaultVar(cfg: dict):
    dataDir = Path(cfg["DATA_FOLDER"])
    jingleDir = Path(cfg["JINGLE_FOLDER"]) if ('JINGLE_FOLDER' in cfg) else 'jingle'

    var = {
        'askForExit': False,
        'languages': ['ru', 'uk', 'en'],
        'ru': {
            'type': 'silero',
            'name': 'Русский язык',
            'model': None,
            'url': 'https://models.silero.ai/models/tts/ru/v3_1_ru.pt',
            'female': 'xenia',
            'male': 'aidar',
            'default': 'xenia',
            'phrase': 'В недрах тундры выдры в г+етрах т+ырят в вёдра +ядра к+едров.' 
        },
        'uk': {
            'type': 'silero',
            'name': 'Українська мова',
            'model': None,
            'url': 'https://models.silero.ai/models/tts/ua/v3_ua.pt',
            'female': None,
            'male': 'mykyta',
            'default': 'mykyta',
            'phrase': 'О котрій годині ми зустрічаємося? Звучить непогано.' 
        },
        'en': {
            'type': 'silero',
            'name': 'English language',
            'model': None,
            'url': 'https://models.silero.ai/models/tts/en/v3_en.pt',
            'female': 'en_0',
            'male': 'en_2',
            'default': 'en_0',
            'phrase': 'London is the capital of Great Britain.' 
        },
        'sample_rate': 24000,
        'put_accent': True,
        'put_yo': True,
        'tmp': dataDir / 'tmp',
        'queue': dataDir / 'queue',
        'gen': dataDir / 'generate',
        'jingle': jingleDir,
        'formats': {
            'mp3': 'libmp3lame',
            'ogg': 'libvorbis',
            'm4b': 'aac',
            'opus':'opus'
        },
        'warning': {
            'cuda': None
        }
    }

    var.update(
        genjson = var['gen'] / 'book.json',
        genwav = var['gen'] / 'wav',
        genout = var['gen'] / 'output'
    )

    return var
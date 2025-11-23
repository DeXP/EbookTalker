import sys
from pathlib import Path
from helpers.DownloadItem import DownloadItem


def GetDefaultVar(cfg: dict) -> dict:
    dataDir = Path(cfg["DATA_FOLDER"])
    jingleDir = Path(cfg["JINGLE_FOLDER"]) if ('JINGLE_FOLDER' in cfg) else 'jingle'

    sileroUrl = 'https://github.com/DeXP/EbookTalker/releases/download/silero/'
    coquiUrl  = 'https://github.com/DeXP/EbookTalker/releases/download/coqui-ai-tts/'
    torchUrl  = 'https://github.com/DeXP/EbookTalker/releases/download/torch-2.8-cuda/'
    torchPath = str(Path(sys.executable).parent)

    var = {
        'askForExit': False,
        'loading': '',
        'languages': {
            'ru': DownloadItem(
                group = "silero",
                name = "Русский",
                subtitle = 'Russian',
                url = sileroUrl + "v3_1_ru.pt",
                sha256 = "cf60b47ec8a9c31046021d2d14b962ea56b8a5bf7061c98accaaaca428522f85",
                dest = "MODELS_FOLDER",
                size = 61896251,
                extra = {
                    'model': None,
                    'female': 'xenia',
                    'male': 'aidar',
                    'default': 'xenia',
                    'phrase': 'В недрах тундры выдры в г+етрах т+ырят в вёдра +ядра к+едров.' 
                }
            ),
            'en': DownloadItem(
                group = "silero",
                name = "English",
                subtitle = 'English',
                url = sileroUrl + "v3_en.pt",
                sha256 = "02b71034d9f13bc4001195017bac9db1c6bb6115e03fea52983e8abcff13b665",
                dest = "MODELS_FOLDER",
                size = 57194546,
                extra = {
                    'model': None,
                    'female': 'en_0',
                    'male': 'en_2',
                    'default': 'en_0',
                    'phrase': 'London is the capital of Great Britain.'
                }
            ),
            'uk': DownloadItem(
                group = "silero",
                name = "Українська",
                subtitle = 'Ukrainian',
                url = sileroUrl + "v3_ua.pt",
                sha256 = "025c53797e730142816c9ce817518977c29d7a75adefece9f3c707a4f4b569cb",
                dest = "MODELS_FOLDER",
                size = 57081646, 
                extra = {
                    'model': None,
                    'female': None,
                    'male': 'mykyta',
                    'default': 'mykyta',
                    'phrase': 'О котрій годині ми зустрічаємося? Звучить непогано.' 
                }
            ),
            'fr': DownloadItem(
                group = "silero",
                name = "Français",
                subtitle = 'French',
                url = sileroUrl + "v3_fr.pt",
                sha256 = "02ed062cfff1c7097324929ca05c455a25d4f610fd14d51b89483126e50f15cb",
                dest = "MODELS_FOLDER",
                size = 57085158,
                extra = {
                    'model': None,
                    'female': 'fr_5',
                    'male': 'fr_0',
                    'default': 'fr_5',
                    'phrase': 'Je suis ce que je suis, et si je suis ce que je suis, qu’est ce que je suis.'
                }
            ),
            'de': DownloadItem(
                group = "silero",
                name = "Deutsch",
                subtitle = 'Deutsch',
                url = sileroUrl + "v3_de.pt",
                sha256 = "2e22f38619e1d1da96d963bda5fab6d53843e8837438cb5a45dc376882b0354b",
                dest = "MODELS_FOLDER",
                size = 57076082,
                extra = {
                    'model': None,
                    'english': 'Deutsch',
                    'female': 'eva_k',
                    'male': 'bernd_ungerer',
                    'default': 'eva_k',
                    'phrase': 'Fischers Fritze fischt frische Fische, Frische Fische fischt Fischers Fritze.' 
                }
            ),
            'es': DownloadItem(
                group = "silero",
                name = "Español",
                subtitle = 'Spanish',
                url = sileroUrl + "v3_es.pt",
                sha256 = "36206add75fb89d0be16d5ce306ba7a896c6fa88bab7e3247403f4f4a520eced",
                dest = "MODELS_FOLDER",
                size = 57079302,
                extra = {
                    'model': None,
                    'female': None,
                    'male': 'es_1',
                    'default': 'es_1',
                    'phrase': 'Hoy ya es ayer y ayer ya es hoy, ya llegó el día, y hoy es hoy.'
                }
            ),
        },
        'coqui-ai': {
            'xtts_v2': DownloadItem(
                group = "coqui-ai",
                name = "XTTS v2",
                url = coquiUrl + "xtts_v2.7z",
                sha256 = "c087ed6c6a5c6834a07a97e44224e28c9b62975ca7ba32098284c5358e955f49",
                dest = "MODELS_FOLDER",
                size = 1695868275,
                description = "en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi",
                extra = {
                    'model': None,
                    'female': 'Ana Florence',
                    'male': 'Aaron Dreschner',
                    'default': 'Ana Florence'
                }
            ),
        },
        'torch' : {
            'cuda129': DownloadItem(
                group = "torch",
                name = "CUDA 12.9 Runtime (PyTorch 2.8)",
                url = torchUrl + "EbookTalker-Torch-2.8.0+cu129.7z",
                size = 1968960562,
                dest = torchPath,
                needs_admin = True,
                description = "RTX 20xx/30xx/40xx, A100, A40 (fastest)",
                sha256 = "6a393dc49428304a73aa4cdd229dbd3f99144fe5ea15c456201b3af26196e2fd"
            ),
            'cuda126': DownloadItem(
                group = "torch",
                name = "CUDA 12.6 Runtime (PyTorch 2.8)",
                url = torchUrl + "EbookTalker-Torch-2.8.0+cu126.7z",
                size = 1465104447,
                dest = torchPath,
                needs_admin = True,
                description = "GTX 10xx, Quadro P series",
                sha256 = "3fb1b4948c69794297358398aafaf7260c8f69dd4c3ac84437303275e5422825"
            ),
            'cpu': DownloadItem(
                group = "torch",
                name = "CPU-only PyTorch 2.8",
                url = torchUrl + "EbookTalker-Torch-2.8.0+cpu.7z",
                size = 57973929,
                dest = torchPath,
                needs_admin = True,            
                sha256 = "a67b91651fa9a46e3c5b1c7a76ba7219362db1d70fdc5c0e7af32f9da790e483",
                description = "AMD/Intel GPUs or no NVIDIA (slower)"
            )
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
        'torchInternalPath': torchPath, 
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
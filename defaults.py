import sys
from pathlib import Path
from helpers.DownloadItem import DownloadItem


def GetDefaultVar(cfg: dict):
    dataDir = Path(cfg["DATA_FOLDER"])
    jingleDir = Path(cfg["JINGLE_FOLDER"]) if ('JINGLE_FOLDER' in cfg) else 'jingle'

    sileroUrl = 'https://github.com/DeXP/EbookTalker/releases/download/silero/'
    torchUrl  = 'https://github.com/DeXP/EbookTalker/releases/download/torch-2.8-cuda/'
    torchPath = str(Path(sys.executable).parent / "_internal")

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
                dest = "models",
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
                dest = "models",
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
                dest = "models",
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
                dest = "models",
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
                dest = "models",
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
                dest = "models",
                extra = {
                    'model': None,
                    'female': None,
                    'male': 'es_1',
                    'default': 'es_1',
                    'phrase': 'Hoy ya es ayer y ayer ya es hoy, ya llegó el día, y hoy es hoy.'
                }
            ),
        },
        'torch' : {
            'cuda129': DownloadItem(
                group = "torch",
                name = "CUDA 12.9 Runtime (PyTorch 2.8)",
                url = torchUrl +"EbookTalker-Torch-2.8.0+cu129.7z",
                dest = torchPath,
                needs_admin = True,
                description = "For RTX 20xx/30xx/40xx, A100, A40 (fastest)",
                sha256 = "1a8c2b7eac585bc439be1d6f17e18a6f1a9fb1969bd3045a9f9957a96cc9e483"
            ),
            'cuda126': DownloadItem(
                group = "torch",
                name = "CUDA 12.6 Runtime (PyTorch 2.8)",
                url = torchUrl + "EbookTalker-Torch-2.8.0+cu126.7z",
                dest = torchPath,
                needs_admin = True,
                description = "For GTX 10xx, Quadro P series",
                sha256 = "d27eba20953103c9773932facb4b8e84bde7a5c8d03a2b12afa96a08bfe7788d"
            ),
            'cpu': DownloadItem(
                group = "torch",
                name = "CPU-only PyTorch 2.8",
                url = torchUrl + "EbookTalker-Torch-2.8.0+cpu.7z",
                dest = torchPath,
                needs_admin = True,            
                sha256 = "ac1243950fb61f850d4c6ad7706b52782b6caa581eec6dbe187d9193e2ff4860",
                description = "For AMD/Intel GPUs or no NVIDIA (slower)"
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
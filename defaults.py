import sys
from pathlib import Path
from helpers.DownloadItem import DownloadItem


def GetDefaultVar(cfg: dict) -> dict:
    dataDir = Path(cfg["DATA_FOLDER"])
    jingleDir = Path(cfg["JINGLE_FOLDER"]) if ('JINGLE_FOLDER' in cfg) else 'jingle'

    sileroUrl = 'https://github.com/DeXP/EbookTalker/releases/download/silero/'
    coquiUrl  = 'https://github.com/DeXP/EbookTalker/releases/download/coqui-ai-tts/'
    torchUrl  = 'https://github.com/DeXP/EbookTalker/releases/download/torch-2.9.1/'
    torchPath = str(Path(sys.executable).parent)

    var = {
        'askForExit': False,
        'loading': '',
        'languages': {
            'ru': DownloadItem(
                group = "silero",
                name = "Русский",
                subtitle = 'v3.1, Russian',
                url = sileroUrl + "v3_1_ru.pt",
                sha256 = "cf60b47ec8a9c31046021d2d14b962ea56b8a5bf7061c98accaaaca428522f85",
                dest = "MODELS_FOLDER",
                size = 61896251,
                extra = {
                    'model': None,
                    'female': 'xenia',
                    'male': 'aidar',
                    'default': 'xenia',
                    'accentors': ['Silero Stress', 'RUaccent tiny', 'RUaccent tiny2', 'RUaccent tiny2.1', 'RUaccent turbo3', 'RUaccent turbo3.1', 'RUaccent turbo', 'RUaccent big_poetry'],
                    'phrase': 'В недрах тундры выдры в г+етрах т+ырят в вёдра +ядра к+едров.' 
                }
            ),
            'en': DownloadItem(
                group = "silero",
                name = "English",
                subtitle = 'v3, English',
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
                subtitle = 'v3, Ukrainian',
                url = sileroUrl + "v3_ua.pt",
                sha256 = "025c53797e730142816c9ce817518977c29d7a75adefece9f3c707a4f4b569cb",
                dest = "MODELS_FOLDER",
                size = 57081646, 
                extra = {
                    'model': None,
                    'female': None,
                    'male': 'mykyta',
                    'default': 'mykyta',
                    'accentors': ['Silero Stress'],
                    'phrase': 'О котрій годині ми зустрічаємося? Звучить непогано.' 
                }
            ),
            'fr': DownloadItem(
                group = "silero",
                name = "Français",
                subtitle = 'v3, French',
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
                subtitle = 'v3, Deutsch',
                url = sileroUrl + "v3_de.pt",
                sha256 = "2e22f38619e1d1da96d963bda5fab6d53843e8837438cb5a45dc376882b0354b",
                dest = "MODELS_FOLDER",
                size = 57076082,
                extra = {
                    'model': None,
                    'female': 'eva_k',
                    'male': 'bernd_ungerer',
                    'default': 'eva_k',
                    'phrase': 'Fischers Fritze fischt frische Fische, Frische Fische fischt Fischers Fritze.' 
                }
            ),
            'es': DownloadItem(
                group = "silero",
                name = "Español",
                subtitle = 'v3, Spanish',
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
            'cis': DownloadItem(
                group = "silero",
                name = "CIS",
                subtitle = 'v5, Multilingual',
                url = sileroUrl + "v5_cis_base_nostress.pt",
                sha256 = "3981ab3d72fb3534cf390a1735e346c48c11a58ce86b5cd2412204941c796c98",
                description = "aze, hye, bak, bel, kat, kbd, kaz, xal, kir, mdf, ru, tgk, tat, udm, uzb, ukr, kjh, chv, erz, sah",
                dest = "MODELS_FOLDER",
                size = 91701321,
                extra = {
                    'model': None,
                    'langs': {
                        'az':  {'native': 'aze', 'voice': 'aze_gamat',    'name': 'Azerbaijani' , 'accentors': ['Silero Simple'], 'phrase': 'Мән һәр сәһәр еркән галхыб тәзә һава ылә мәшг едырәм.' },
                        'hy':  {'native': 'hye', 'voice': 'hye_zara',     'name': 'Armenian'    , 'accentors': ['Silero Simple'], 'phrase': 'Ես շաբաթ օրերին սիրում եմ երկար զբոսնել անտառով:' },
                        'ba':  {'native': 'bak', 'voice': 'bak_aigul',    'name': 'Bashkir'     , 'accentors': ['Silero Simple'], 'phrase': 'Күп балалыларға былайҙа сертификат бирелә бит.' },
                        'be':  {'native': 'bel', 'voice': 'bel_anatoliy', 'name': 'Belarus'     , 'accentors': ['Silero Stress'], 'phrase': 'В+ечарам +я любл+ю чыт+аць цік+авыя кн+ігі пры святл+е начнік+а.' },
                        'ka':  {'native': 'kat', 'voice': 'kat_vika',     'name': 'Georgian'    , 'accentors': ['Silero Simple'], 'phrase': 'მე ძალიან მიყვარს ჩემი ოჯახის წევრებთან ერთად დროის გატარება.' },
                        'kbd': {'native': 'kbd', 'voice': 'kbd_eduard',   'name': 'Kab.-Cherkes', 'accentors': ['Silero Simple'], 'phrase': 'Сэ уиӀуанэ уашъхъэри унагъуэхэри сэбэп хъущтыр сыту щӀэлъэӀу.' },
                        'kz':  {'native': 'kaz', 'voice': 'kaz_zhadyra',  'name': 'Kazakh'      , 'accentors': ['Silero Simple'], 'phrase': 'Мен балалық шақта жаңа досдармен танысуды әбден ұнататынмын.' },
                        'xal': {'native': 'xal', 'voice': 'xal_kejilgan', 'name': 'Kalmyk'      , 'accentors': ['Silero Simple'], 'phrase': 'Би эцкд сарин җилин дуулҗана хойр седклтә күрәм.' },
                        'ky':  {'native': 'kir', 'voice': 'kir_nurgul',   'name': 'Kyrgyz'      , 'accentors': ['Silero Simple'], 'phrase': 'Мен мектепте окуп жүргөндө эң жакшы досум менен тааныштым.' },
                        'mdf': {'native': 'mdf', 'voice': 'mdf_oksana',   'name': 'Moksha'      , 'accentors': ['Silero Simple'], 'phrase': 'Монь тяштеть эзда кизонь карьхть сельметь кштинь аф лац.' },
                        'ru':  {'native': 'ru',  'voice': 'ru_oksana',    'name': 'Russian'     , 'accentors': ['Silero Stress', 'RUaccent tiny', 'RUaccent tiny2', 'RUaccent tiny2.1', 'RUaccent turbo3', 'RUaccent turbo3.1', 'RUaccent turbo', 'RUaccent big_poetry'], 'phrase': 'В недрах тундры выдры в г+етрах т+ырят в вёдра +ядра к+едров.' },
                        'tg':  {'native': 'tgk', 'voice': 'tgk_safarhuja','name': 'Tajik'       , 'accentors': ['Silero Simple'], 'phrase': 'Ман дар бораи хонаи нави худ дар канори дарё хондем.' },
                        'tt':  {'native': 'tat', 'voice': 'tat_albina',   'name': 'Tatar'       , 'accentors': ['Silero Simple'], 'phrase': 'Мин ерак түгел урман эчендә чиста һавада йөргәне яратам.' },
                        'udm': {'native': 'udm', 'voice': 'udm_bogdan',   'name': 'Udmurt'      , 'accentors': ['Silero Simple'], 'phrase': 'Мон ашалэ тӥлед нуналлы огы быдэсэ кошко учке.' },
                        'uz':  {'native': 'uzb', 'voice': 'uzb_saida',    'name': 'Uzbek'       , 'accentors': ['Silero Simple'], 'phrase': 'Мен болалигимда кўпинча дўстларим билан ҳовлида футбол ўйнардим.' },
                        'uk':  {'native': 'ukr', 'voice': 'ukr_igor',     'name': 'Ukrainian'   , 'accentors': ['Silero Stress'], 'phrase': '+Я з р+аннього дит+инства д+уже любл+ю сл+ухати цік+аві к+азки.' },
                        'kjh': {'native': 'kjh', 'voice': 'kjh_karina',   'name': 'Khakas'      , 'accentors': ['Silero Simple'], 'phrase': 'Мин аал чоньчарға пастабахсынар хайдиғырам хынаңның хоный.' },
                        'cv':  {'native': 'chv', 'voice': 'chv_ekaterina','name': 'Chuvash'     , 'accentors': ['Silero Simple'], 'phrase': 'Эпĕ ача чухнех пиччĕшсемпе юнашар кĕтӳльех вăйă вылянă.' },
                        'erz': {'native': 'erz', 'voice': 'erz_alexandr', 'name': 'Erzya'       , 'accentors': ['Silero Simple'], 'phrase': 'Монь веленек шачемсёномань панжовксонть кис эрьва кизонь туема.' },
                        'sah': {'native': 'sah', 'voice': 'sah_zinaida',  'name': 'Yakut'       , 'accentors': ['Silero Simple'], 'phrase': 'Мин бүгүн оройунан саһарҕа оонньуу сылдьан сымнаҕыстык утуйбутум.' }
                    }
                },
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
                    'default': 'Ana Florence',
                    'langs': {
                        'en': {'voice': 'Claribel Dervla',  'name': 'English'   , 'phrase': 'London is the capital of Great Britain. And New York is the capital of what?' },
                        'es': {'voice': 'Ana Florence',     'name': 'Spanish'   , 'phrase': 'Habla usted otras lenguas además del español?' },
                        'fr': {'voice': 'Gitta Nikolina',   'name': 'French'    , 'phrase': "Est-ce que vous pourriez parler plus lentement, s'il vous plaît?" },
                        'de': {'voice': 'Gracie Wise',      'name': 'German'    , 'phrase': 'Sprechen Sie eine andere Sprache als Deutsch?' },
                        'it': {'voice': 'Tammie Ema',       'name': 'Italian'   , 'phrase': "Parli un'altra lingua oltre l'italiano?" },
                        'pt': {'voice': 'Alison Dietlinde', 'name': 'Portuguese', 'phrase': 'O senhor poderia escrever isso para mim, por favor' },
                        'pl': {'voice': 'Lidiya Szekeres',  'name': 'Polish'    , 'phrase': 'Bóbr zwyczajny – gatunek ziemno-wodnego gryzonia z rodziny bobrowatych' },
                        'tr': {'voice': 'Tanja Adelina',    'name': 'Turkish'   , 'phrase': "Helva, Balkan ülkelerinde ve pek çok Orta Doğu ülkesinde yaygın bir tatlı" },
                        'ru': {'voice': 'Vjollca Johnnie',  'name': 'Russian'   , 'phrase': 'В недрах тундры выдры в гетрах тырят в вёдра ядра кедров'  },
                        'nl': {'voice': 'Gitta Nikolina',   'name': 'Dutch'     , 'phrase': 'Zou u het voor mij willen opschrijven, alstublieft?' },
                        'cs': {'voice': 'Lidiya Szekeres',  'name': 'Czech'     , 'phrase': 'Šalina je kolejové vozidlo, převážně určené pro provoz v městských ulicích' },
                        'ar': {'voice': 'Suad Qasim',       'name': 'Arabic'    , 'phrase': 'هل تتكلم اللغة العربية؟' },
                        'hu': {'voice': 'Lidiya Szekeres',  'name': 'Hungarian' , 'phrase': 'Örülök, hogy megismertelek Örvendek' },
                        'hi': {'voice': 'Royston Min',      'name': 'Hindi'     , 'phrase': 'कृपया भोजन का आनंद लीजिये!' },
                        # # Additional modules needs to be installed and configured - would be added later # #
                        #'ko':{'voice': 'Kazuhiko Atallah', 'name': 'Korean'    , 'phrase': '이병철 창업주가 삼성물산이라는 이름으로 자본금 3만 원에 회사을 창업하여 현재의 삼성그룹으로 발전하였다' },
                        #'ja':{'voice': 'Kazuhiko Atallah', 'name': 'Japanese'  , 'phrase': '沖縄県 は、日本の九州・沖縄地方に位置する県。県庁所在地は那覇市。旧琉球王国。' },
                        #'zh-cn':{'voice': 'Kazuhiko Atallah', 'name': 'Chinese (Simplified)', 'phrase': '这个用汉语怎么说？' }
                    }
                }
            ),
        },
        'torch' : {
            'cuda130': DownloadItem(
                group = "torch",
                name = "CUDA 13.0 Runtime (PyTorch 2.10.0)",
                url = torchUrl + "EbookTalker-Torch-2.10.0+cu130.7z",
                size = 1586580546,
                dest = torchPath,
                needs_admin = True,
                description = "RTX 40xx, A100, A40, L4, H100",
                sha256 = "52cbb7d29234bb89190c55ef550f3562706b51e2f7ba12e94bacbcbc3b3bcd48"
            ),
            'cuda126': DownloadItem(
                group = "torch",
                name = "CUDA 12.6 Runtime (PyTorch 2.10.0)",
                url = torchUrl + "EbookTalker-Torch-2.10.0+cu126.7z",
                size = 1519956102,
                dest = torchPath,
                needs_admin = True,
                description = "RTX 20xx/30xx, GTX 10xx/16xx, Titan RTX, Quadro RTX, T4, A2, A10",
                sha256 = "0154d34c39700271b25316ecfce3aac4eeaf4164e335b3dc3081b40fba61371c"
            ),
            'cpu': DownloadItem(
                group = "torch",
                name = "CPU-only PyTorch 2.10.0",
                url = torchUrl + "EbookTalker-Torch-2.10.0+cpu.7z",
                size = 59444934,
                dest = torchPath,
                needs_admin = True,            
                sha256 = "c3b60d38cc7819bfd693a107bd1018dc562db6bca4f109711b6735e25c5a0528",
                description = "AMD/Intel GPUs or no NVIDIA"
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
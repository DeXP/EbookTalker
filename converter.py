import os, re, torch, time, base64
from pathlib import Path

from helpers import settings, book, dxfs, dxaudio, dxsplitter, dxnormalizer

#from sentence_splitter import SentenceSplitter
#from accentru import predictor


def Init(cfg: dict):
    # accentRuPredictor = predictor.Predictor('accentru/model-accentru.onnx', 'accentru/vocab-accentru.json', 'accentru/ru_stress_compressed.txt')

    dataDir = Path(cfg["DATA_FOLDER"])

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
        #'accent_ru': accentRuPredictor,
        'sample_rate': 24000,
        'put_accent': True,
        'put_yo': True,
        'tmp': dataDir / 'tmp',
        'queue': dataDir / 'queue',
        'gen': dataDir / 'generate',
        'jingle': Path(cfg["JINGLE_FOLDER"]),
        'formats': {
            'mp3': 'libmp3lame',
            'ogg': 'vorbis',
            'm4b': 'aac',
            'opus':'opus'
        }
    }

    var.update(
        genfb2 = var['gen'] / 'book.fb2',
        genwav = var['gen'] / 'wav',
        genout = var['gen'] / 'output'
    )

    var['tmp'].mkdir(parents=True, exist_ok=True)
    dxfs.CreateDirectory(var['tmp'], var['queue'])
    dxfs.CreateDirectory(var['tmp'], Path('models'))


    var['settings'] = settings.LoadOrDefault(cfg, var)

    device = torch.device(var['settings']['app']['processor'])
    num_threads = int(var['settings']['app']['threads'])
    if num_threads > 0:
        torch.set_num_threads(num_threads)
    var['device'] = device

    PreloadModel(var, 'ru')
    # PreloadModel(var, 'en')

    return var


def PreloadModel(var: dict, lang = 'ru'):
    if lang in var:
        urlPath = Path(var[lang]['url'])
        modelName = urlPath.name
        local_file = 'models/' + modelName

        if not os.path.isfile(local_file):
            torch.hub.download_url_to_file(var[lang]['url'], local_file)

        if (".pt" == urlPath.suffix):
            var[lang]['model'] = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
            var[lang]['model'].to(var['device'])
        elif ("jit" in modelName):
            var[lang]['model'] = torch.jit.load(local_file)
            var[lang]['model'].eval()
            torch._C._jit_set_profiling_mode(False) 
            torch.set_grad_enabled(False)
            var[lang]['model'].to(var['device'])

        symb = var[lang]['model'].symbols
        var[lang]['symbols'] = re.compile(f"[{symb}]", re.IGNORECASE)


def GetModel(var: dict, lang = 'ru'):
    if (lang in var) and ('model' in var[lang]) and (var[lang]['model'] is None):
        PreloadModel(var, lang)
    return var[lang]['model']


def GetSupportedAudioFormats(cfg: dict, var: dict):
    all_encoders = dxaudio.get_supported_encoders(cfg)
    supported = []
    for format, encoder in var['formats'].items():
        if encoder in all_encoders:
            supported.append(format)
    return supported


def IsCorrectPhrase(var: dict, lang = 'ru', text = ''):
    if text and (lang in var) and ('symbols' in var[lang]):
        if re.search(var[lang]['symbols'], text):
            return True
    return False


def DownloadFile(fromUrl: str, toFile: Path):
    torch.hub.download_url_to_file(fromUrl, str(toFile))


def getBooks(var: dict):
    return sorted(var['queue'].glob("*.*"), key=os.path.getmtime)


def getJingles(var: dict):
    return sorted(var['jingle'].glob("*.wav"))


def fillQueue(que, var: dict):
    que[:] = [] # que.clear()
    files = getBooks(var)
    for f in files:
        if f.is_file():
            info, _ = book.ParseBook(f)
            que.append(info)


def MoveEbookToGenerate(file: Path, var: dict):
    # dxfs.CreateDirectory(var['tmp'], var['gen'])
    var['gen'].mkdir(parents=True, exist_ok=True)
    # dxfs.MoveFile(var['tmp'], file, var['genfb2'])
    if var['genfb2'].exists():
        var['genfb2'].unlink()
    file.rename(var['genfb2'])



def GeneratePause(var, timeMs = 300, name = "pause.wav"):
    var['ru']['model'].save_wav(ssml_text=f'<speak><break time="{timeMs}ms"/></speak>',
                speaker=var['ru']['default'],
                sample_rate=var['sample_rate'],
                audio_path=str(var['genwav'] / name))


def ProcessSentence(lang, number, sentence, var):
    wavFile = var['genwav'] / f"{number}.wav"
    speaker = var['settings']['silero'][lang]['voice']
    return SayText(wavFile, lang, speaker, sentence, var)


def SayText(wavFile, lang, speaker, text, var):
    if IsCorrectPhrase(var, lang, text) and (not wavFile.exists()):
        # Generate
        # print(text)
        try:
            GetModel(var, lang).save_wav(text=text,
                speaker = speaker,
                sample_rate=var['sample_rate'],
                put_accent=var['put_accent'],
                put_yo=var['put_yo'],
                audio_path=str(wavFile))
        except Exception as error:
            print(f"Cannot save WAV for sentence {wavFile}: '{text}'. Error: {error}")
            return False
        return True    
    return wavFile.exists()



def ConvertBook(file: Path, outputDirPath, dirFormat, proc, cfg, var):
    dxfs.CreateDirectory(var['tmp'], var['gen'])
    dxfs.CreateDirectory(var['tmp'], var['genwav'])
    dxfs.CreateDirectory(var['tmp'], var['genout'])
    proc['file'] = file.name
    proc['status'] = 'process'

    codec = var['settings']['app']['codec']
    encoder = var['formats'][codec]

    info, coverBytes = book.ParseBook(file, full = True)
    proc['bookName'] = book.BookName(info, includeAuthor=True)
    lang = info['lang'] if ('lang' in info) else 'ru'

    if ('error' in info) and info['error']:
        error = info['error']
        failure = info['failure'] if 'failure' in info else ''
        proc['status'] = 'error'
        raise Exception(f"{error}: {failure}")
    
    cover = None
    if coverBytes:
        width, height, _, _, coverType = dxaudio.get_image_info(coverBytes)
        cover = var['genout'] / f"cover.{coverType}"
        proc['coverWidth'] = width
        proc['coverHeight'] = height
        if not cover.exists():                   
            with open(str(cover.absolute()), 'wb') as f:
                f.write(coverBytes)

    author = book.SafeAuthorName(info)

    jingles = getJingles(var)

    sectionCount = 0
    tagCount = 0
    sentenceCount = 0

    totalTagsCount = 0
    totalSencenceCount = 0
    for section in info['sections']:
        totalTagsCount += len(section['text'])
        for p in section['text']:
            totalSencenceCount += len(p)

    proc['totalLines'] = totalTagsCount
    proc['totalSentences'] = totalSencenceCount

    GeneratePause(var, 300, "pause.wav")
    GeneratePause(var, 500, "pause-long.wav")

    for section in info['sections']:
        sectionCount += 1
        sectionWavs = []    
        rawSectionTitle = section['title']
        sectionTitle = dxnormalizer.normalize(rawSectionTitle, lang)
        # print(f"Section {sectionCount} ({len(section)}): {sectionTitle}")
        proc['sectionTitle'] = sectionTitle
        if sectionTitle:
            sentenceCount += 1
            if ProcessSentence(lang, sentenceCount, sectionTitle, var):
                sectionWavs.append(f"{sentenceCount}.wav")
                sectionWavs.append("pause-long.wav")

        # Process each paragraph
        for p in section['text']:
            tagCount += 1
            proc['lineNumber'] = tagCount
            proc['lineSentenceCount'] = len(p)

            #print(sentences)
            lineSentence = 0
            for s in p:
                lineSentence += 1
                sentenceCount += 1
                proc['lineSentenceNumber'] = lineSentence
                proc['sentenceNumber'] = sentenceCount
                proc['sentenceText'] = s
                if ProcessSentence(lang, sentenceCount, s, var):
                    sectionWavs.append(f"{sentenceCount}.wav")
                    # last senctence in paragraph - long pause
                    pauseName = "pause-long.wav" if lineSentence == (len(p) - 1) else 'pause.wav'
                    sectionWavs.append(pauseName)
                if var['askForExit']:
                    break
            if var['askForExit']:
                break
        if var['askForExit']:
            break

        # All sentences processed - concatenate the section into one file
        codec = cfg['AUDIO_CODEC']
        encoder = var['formats'][codec]
        sectionWavFile = var['genout'] / f"{sectionCount}.wav"
        sectionCompressedFile = var['genout'] / f"{sectionCount}.{codec}"

        compressedExists = sectionCompressedFile.exists() and (sectionCompressedFile.stat().st_size > 0)
        if not compressedExists:
            if not sectionWavFile.exists():
                if (len(sectionWavs) > 10) and (len(jingles) > 0):
                    # Add chapter jingle
                    jingleNum = (sectionCount - 1) % len(jingles)
                    curJingle = jingles[jingleNum]
                    sectionWavs.append(curJingle.absolute())
                
                dxaudio.concatenate_wav_files(var['genwav'], sectionWavs, sectionWavFile)
            curTitle = sectionTitle if sectionTitle else proc['bookName']
            dxaudio.convert_wav_to_compressed(encoder, cfg, sectionWavFile, sectionCompressedFile, title=curTitle, author=author, cover=cover, info=info)
            if sectionCompressedFile.exists() and (sectionCompressedFile.stat().st_size > 0):
               sectionWavFile.unlink()

    if var['askForExit']:
        return
    
    # Done. Move output
    outputDir = Path(outputDirPath)
    if "full" == dirFormat.lower():
        # Full format - create sub folders
        bookName = book.SafeBookName(info, includeAuthor=False)
        if ('sequence' in info) and info['sequence']:
            outputDir = Path(outputDirPath) / author / book.SafeFileName(info['sequence']) / bookName
        else:
            outputDir = Path(outputDirPath) / author / bookName
    else:
        # Short - all books into same folder
        outputDir = Path(outputDirPath) / book.SafeBookName(info, includeAuthor=True)
    
    dxfs.CreateDirectory(var['tmp'], outputDir)
    dxfs.MoveAllFiles(var['tmp'], var['genout'], outputDir)

    dxfs.RemoveDirectoryRecursively(var['genout'])
    dxfs.RemoveDirectoryRecursively(var['genwav'])
    dxfs.RemoveDirectoryRecursively(var['gen'])

    proc.clear()
    proc['error'] = ''



def ConverterLoop(que, proc, cfg, var):
    proc['error'] = ''

    fillQueue(que, var)

    while not var['askForExit']:
        if not var['genfb2'].is_file():
            # Pick up the first book
            books = getBooks(var)
            if len(books) > 0:
                initFB2 = books[0]
                MoveEbookToGenerate(initFB2, var)
                fillQueue(que, var)
            else:
                proc['status'] = 'idle'
                proc['ffmpeg'] = dxaudio.get_ffmpeg_exe(cfg)
                time.sleep(3)

        if var['genfb2'].is_file():
            outputFolder = var['settings']['app']['output']
            directoriesFormat = var['settings']['app']['dirs']
            ConvertBook(var['genfb2'], outputFolder, directoriesFormat, proc, cfg, var)
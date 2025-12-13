import os, re, json, torch, time
from pathlib import Path

from helpers import book, dxfs, dxaudio, dxnormalizer
from silero_stress import load_accentor, simple_accentor


def InitModels(cfg: dict, var: dict):
    var['tmp'].mkdir(parents=True, exist_ok=True)
    dxfs.CreateDirectory(var['tmp'], var['queue'])
    dxfs.CreateDirectory(var['tmp'], Path('models'))

    cudaWarning = get_cuda_version_warning()
    useCuda = cudaWarning is None

    var['useCuda'] = useCuda
    var['warning']['cuda'] = cudaWarning

    device = torch.device('cuda' if useCuda else 'cpu')
    if not useCuda:
        torch.set_num_threads(os.cpu_count())
    var['device'] = device

    if 'silero' != var['settings']['app']['engine']:
        PreloadModel(cfg, var, 'en')


def GetSileroModelExt(cfg: dict, var: dict, lang: str = 'ru', strict: bool = False, allowUninstalled: bool = True):
    if lang in var['languages']:
        modelPath = GetModelPathByName(cfg, Path(var['languages'][lang].url).name)
        if allowUninstalled or modelPath.exists():
            return var['languages'][lang]
    if not strict:
        for lang_key, language in var['languages'].items():
            if ('langs' in language.extra) and (lang in language.extra['langs']):
                modelPath = GetModelPathByName(cfg, Path(language.url).name)
                if allowUninstalled or modelPath.exists():
                    return language
    return None


def GetSileroModel(cfg: dict, var: dict, lang: str = 'ru', strict: bool = False):
    model = GetSileroModelExt(cfg, var, lang, strict, allowUninstalled=False)
    if model is None:
        model = GetSileroModelExt(cfg, var, lang, strict, allowUninstalled=True)
    return model


def GetSileroAccentor(cfg: dict, var: dict, lang: str = 'ru'):
    model = GetSileroModel(cfg, var, lang)
    if model is None:
        return None
    if 'langs' in model.extra:
        sub_lang = model.extra['langs'].get(lang, None)
        if sub_lang:
            if (not 'accentor' in model.extra['langs'][lang]) or (model.extra['langs'][lang]['accentor'] is None):
                model.extra['langs'][lang]['accentor'] = LoadSileroAccentor(var, sub_lang['native'])
            return model.extra['langs'][lang]['accentor']
    else:
        # Single language model
        if 'ru' == lang:
            return None
        if 'uk' == lang:
            lang = 'ukr'
        if (not 'accentor' in model.extra) or (model.extra['accentor'] is None):
            model.extra['accentor'] = LoadSileroAccentor(var, lang)
        return model.extra['accentor']
    return None


def LoadSileroAccentor(var: dict, lang: str = 'ru'):
    if lang in ['ru', 'ukr']:
        accentor = load_accentor(lang)
        accentor.to(device='cuda:0' if var['useCuda'] else 'cpu')
        if not var['useCuda']:
            torch.set_num_threads(os.cpu_count())
        return accentor
    if lang in simple_accentor.supported_langs:
        return simple_accentor.SimpleAccentor(lang)
    return None


def GetSileroVoiceExt(cfg: dict, var: dict, lang: str = 'ru', allowUninstalled: bool = True):
    if lang in var['settings']['silero']:
        modelPath = GetModelPathByName(cfg, Path(var['languages'][lang].url).name)
        if allowUninstalled or modelPath.exists():
            return var['settings']['silero'][lang]['voice']
    for lang_key, language in var['languages'].items():
        if ('langs' in language.extra) and (lang in language.extra['langs']):
            modelPath = GetModelPathByName(cfg, Path(language.url).name)
            if allowUninstalled or modelPath.exists():
                return var['settings']['silero'][lang_key][lang]['voice']
    return None


def GetSileroVoice(cfg: dict, var: dict, lang: str = 'ru'):
    voice = GetSileroVoiceExt(cfg, var, lang, allowUninstalled=False)
    if voice is None:
        voice = GetSileroVoiceExt(cfg, var, lang, allowUninstalled=True)
    return voice


def GetModelName(cfg: dict, var: dict, lang = 'ru', engine: str = '', strict: bool = False) -> str:
    if not engine:
        engine = var['settings']['app']['engine']
    if ('silero' == engine):
        model = GetSileroModel(cfg, var, lang, strict)
        if model:
            urlPath = Path(model.url)
            return urlPath.name
        return engine
    else:
        return engine


def GetModelPathByName(cfg: dict, modelName: str) -> Path:
    localFile = Path('models') / modelName
    if localFile.exists():
        return localFile
    return Path(cfg['MODELS_FOLDER']) / modelName


def GetModelPath(cfg: dict, var: dict, lang: str = 'ru', engine: str = '', strict: bool = False) -> Path:
    if not engine:
        engine = var['settings']['app']['engine']
    modelName = GetModelName(cfg, var, lang, engine, strict)
    return GetModelPathByName(cfg, modelName)


def IsModelFileExists(cfg: dict, var: dict, lang: str = 'ru', engine: str = '', strict: bool = False) -> bool:
    return GetModelPath(cfg, var, lang, engine, strict).exists()


def PreloadModel(cfg: dict, var: dict, lang: str = 'ru', engine: str = ''):
    if not engine:
        engine = var['settings']['app']['engine']
    modelPath = GetModelPath(cfg, var, lang, engine)
    local_file = str(modelPath)

    if 'silero' == engine:
        model = GetSileroModel(cfg, var, lang)
        if not os.path.isfile(local_file):
            torch.hub.download_url_to_file(model.url, local_file)

        if (".pt" == modelPath.suffix):
            model.extra['model'] = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
            model.extra['model'].to(var['device'])

        if lang in ['ru', 'uk']:
            GetSileroAccentor(cfg, var, lang)
    else:
        # Coqui TTS
        configPath = modelPath / "config.json"
        if configPath.exists():
            from TTS.api import TTS
            var['coqui-ai'][engine].extra['model'] = TTS(model_path=local_file, config_path=str(configPath), progress_bar=False)
            var['coqui-ai'][engine].extra['model'].to(var['device'])



def GetModel(cfg: dict, var: dict, lang: str = 'ru', engine: str = ''):
    if not engine:
        engine = var['settings']['app']['engine']
    origin = GetSileroModel(cfg, var, lang) if 'silero' == engine else var['coqui-ai'][engine]
    if ('model' in origin.extra) and (origin.extra['model'] is None):
        PreloadModel(cfg, var, lang, engine)
    return origin.extra['model']


def GetSamplerate(cfg: dict, var: dict, engine: str = '') -> int:
    if not engine:
        engine = var['settings']['app']['engine']
    return int(var['sample_rate']) if 'silero' == engine else int(GetModel(cfg, var).synthesizer.output_sample_rate)


def _extract_arch_version(arch_string: str):
    """Extracts the architecture string from a CUDA version"""
    base = arch_string.split("_")[1]
    base = base.removesuffix("a")
    return int(base)


def get_cuda_version_warning():
    incompatible_gpu_warn = """
Found GPU%d %s which is of cuda capability %d.%d.
Minimum and Maximum cuda capability supported by this version of PyTorch is
(%d.%d) - (%d.%d)
    """

    import torch
    if (
        torch.version.cuda is not None and torch.cuda.get_arch_list()
    ):  # on ROCm we don't want this check
        for d in range(torch.cuda.device_count()):
            capability = torch.cuda.get_device_capability(d)
            major = capability[0]
            minor = capability[1]
            name = torch.cuda.get_device_name(d)
            current_arch = major * 10 + minor
            min_arch = min(
                (_extract_arch_version(arch) for arch in torch.cuda.get_arch_list()),
                default=50,
            )
            max_arch = max(
                (_extract_arch_version(arch) for arch in torch.cuda.get_arch_list()),
                default=50,
            )
            if current_arch < min_arch or current_arch > max_arch:
                return incompatible_gpu_warn % (
                        d,
                        name,
                        major,
                        minor,
                        min_arch // 10,
                        min_arch % 10,
                        max_arch // 10,
                        max_arch % 10,
                    )
        return None
    return "CUDA disabled or doesn't supports any architectures"


def GetSupportedAudioFormats(cfg: dict, var: dict):
    all_encoders = dxaudio.get_supported_encoders(cfg)
    supported = []
    for format, encoder in var['formats'].items():
        if encoder in all_encoders:
            supported.append(format)
    return supported


def getBooks(var: dict):
    return sorted(var['queue'].glob("*.*"), key=os.path.getmtime)


def getJingles(cfg: dict, var: dict):
    rate = GetSamplerate(cfg, var)
    folder = var['jingle'] / str(rate)
    return sorted(folder.glob("*.wav"))


def fillQueue(que, var: dict):
    que[:] = [] # que.clear()
    files = getBooks(var)
    for f in files:
        if f.is_file():
            info, _ = book.ParseBook(f)
            que.append(info)


def PreConvertBookForTTS(file: Path, var: dict):
    var['gen'].mkdir(parents=True, exist_ok=True)
    if var['genjson'].exists():
        var['genjson'].unlink()

    info, cover = book.ParseBook(file, full=True)

    with open(str(var['genjson']), 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    file.unlink()
    return info, cover


def GeneratePause(cfg: dict, var: dict, durationMs : int = 300, name : str = "pause.wav"):
    return dxaudio.generate_silence_wav(durationMs, var['genwav'] / name, GetSamplerate(cfg, var))


def ProcessSentence(lang: str, number, sentence: str, cfg: dict, var: dict, engine: str = ''):
    if not engine:
        engine = var['settings']['app']['engine']
    wavFile = var['genwav'] / f"{number}.wav"
    speaker = GetSileroVoice(cfg, var, lang) if 'silero' == engine else var['settings'][engine][lang]['voice']
    return SayText(wavFile, lang, speaker, sentence, cfg, var)


def SayText(wavFile: Path, lang: str, speaker: str, text: str, cfg: dict, var: dict, engine: str = ''):
    if not wavFile.exists():
        if not engine:
            engine = var['settings']['app']['engine']
        try:
            if 'silero' == engine:
                GetModel(cfg, var, lang, engine=engine).save_wav(text=text,
                    speaker = speaker,
                    sample_rate = var['sample_rate'],
                    put_accent = var['put_accent'],
                    put_yo = var['put_yo'],
                    audio_path = str(wavFile))
            else:
                # Coqui TTS
                GetModel(cfg, var, engine=engine).tts_to_file(text=text,
                    speaker = speaker,
                    language = lang,
                    file_path = str(wavFile))
        except Exception as error:
            print(f"Cannot save WAV for sentence {wavFile}: '{text}'. Error: {error}")
            return False
        return True    
    return wavFile.exists()



def ConvertBook(file: Path, info: dict, coverBytes, outputDirStr: str, dirFormat: str, proc: dict, cfg: dict, var: dict):
    dxfs.CreateDirectory(var['tmp'], var['gen'])
    dxfs.CreateDirectory(var['tmp'], var['genwav'])
    dxfs.CreateDirectory(var['tmp'], var['genout'])
    proc['status'] = 'process'

    engine = var['settings']['app']['engine']
    codec = var['settings']['app']['codec']
    bitrate = var['settings']['app']['bitrate']
    encoder = var['formats'][codec]

    if info is None:
        info = json.loads(file.read_text(encoding='utf-8'))
        # info, coverBytes = book.ParseBook(file, full = True)

    proc['bookName'] = book.BookName(info, includeAuthor=True)
    lang = dxnormalizer.unify_lang(info['lang']) if ('lang' in info) else 'ru'
    accentor = GetSileroAccentor(cfg, var, lang) if 'silero' == engine else None

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

    jingles = getJingles(cfg, var)

    isSingleOutput = (dirFormat == 'single')

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

    shortPauseDuration = GeneratePause(cfg, var, int(var['settings']['app']['pause-sentence']), "pause.wav")
    longPauseDuration = GeneratePause(cfg, var, int(var['settings']['app']['pause-paragraph']), "pause-long.wav")

    for section in info['sections']:
        sectionCount += 1
        sectionWavs = []    
        rawSectionTitle = section['title']
        sectionTitle = dxnormalizer.normalize(rawSectionTitle, lang)
        sectionTitle = accentor(sectionTitle) if accentor else sectionTitle
        # print(f"Section {sectionCount} ({len(section)}): {sectionTitle}")
        proc['rawSectionTitle'] = rawSectionTitle
        proc['sectionTitle'] = sectionTitle
        if sectionTitle:
            sentenceCount += 1
            if ProcessSentence(lang, sentenceCount, sectionTitle, cfg, var):
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
                accentedText = accentor(s) if accentor else s
                if ProcessSentence(lang, sentenceCount, accentedText, cfg, var):
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
                
                dxaudio.concatenate_audio_files(cfg, var['genwav'], sectionWavs, sectionWavFile)
            curTitle = rawSectionTitle if rawSectionTitle else proc['bookName']

            if not isSingleOutput:
                dxaudio.convert_wav_to_compressed(encoder, cfg, sectionWavFile, sectionCompressedFile, bitrate=bitrate,
                                                title=curTitle, author=book.AuthorName(info), cover=cover, info=info)
                
                if sectionCompressedFile.exists() and (sectionCompressedFile.stat().st_size > 0):
                    sectionWavFile.unlink()

    if var['askForExit']:
        return
    
    # Done. Move output
    outputName = book.GetOutputName(Path(outputDirStr), info, dirFormat)
    outputDir = outputName.parent if isSingleOutput else outputName
    dxfs.CreateDirectory(var['tmp'], outputDir)

    if isSingleOutput:
        # Concatenate all chapter WAVs in output folder
        outputName = outputName.with_name(f"{outputName.name}.{codec}")
        bookWavFile = var['genout'] / "book.wav"
        bookCompressedFile = var['genout'] / f"book.{codec}"
        chapterWavs = []
        chapterMeta = ''
        time = 0.0
        for i, section in enumerate(info['sections']):
            sectionWavFile = var['genout'] / f"{i + 1}.wav"
            if sectionWavFile.exists() and (sectionWavFile.stat().st_size > 0):
                chapterWavs.append(sectionWavFile.name)
                duration = dxaudio.get_wav_duration(sectionWavFile)
                chapterMeta += dxaudio.get_chapter_metadata_str(time, duration, section['title'])
                time += duration

        dxaudio.concatenate_audio_files(cfg, var['genout'], chapterWavs, bookWavFile)
        dxaudio.convert_wav_to_compressed(encoder, cfg, bookWavFile, bookCompressedFile, bitrate=bitrate,
            title=book.BookName(info, includeAuthor=False), author=book.AuthorName(info), cover=cover, info=info, chapters=chapterMeta)
        
        dxfs.MoveFile(var['tmp'], bookCompressedFile, outputName)

    else:
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

        info, cover = None, None

        if not var['genjson'].is_file():
            # Pick up the first book
            books = getBooks(var)
            if len(books) > 0:
                initFB2 = books[0]
                info, cover = PreConvertBookForTTS(initFB2, var)
                fillQueue(que, var)
            else:
                proc['status'] = 'idle'
                proc['ffmpeg'] = dxaudio.get_ffmpeg_exe(cfg)
                time.sleep(3)

        if var['genjson'].is_file():
            outputFolder = var['settings']['app']['output']
            directoriesFormat = var['settings']['app']['dirs']
            ConvertBook(var['genjson'], info, cover, outputFolder, directoriesFormat, proc, cfg, var)
     
import os, re, json, torch, time
from pathlib import Path

from helpers import book, dxfs, dxaudio, dxsplitter, dxnormalizer
from silero_stress import load_accentor


def InitModels(cfg: dict, var: dict):
    var['tmp'].mkdir(parents=True, exist_ok=True)
    dxfs.CreateDirectory(var['tmp'], var['queue'])
    dxfs.CreateDirectory(var['tmp'], Path('models'))

    var['accentor'] = load_accentor()

    cudaWarning = get_cuda_version_warning()
    useCuda = cudaWarning is None

    var['useCuda'] = useCuda
    var['warning']['cuda'] = cudaWarning

    device = torch.device('cuda' if useCuda else 'cpu')
    if not useCuda:
        torch.set_num_threads(os.cpu_count())
    var['device'] = device

    PreloadModel(cfg, var, 'ru')
    # PreloadModel(var, 'en')


def GetModelPath(cfg: dict, var: dict, lang = 'ru') -> Path:
    if lang in var['languages']:
        urlPath = Path(var['languages'][lang].url)
        modelName = urlPath.name

        localFile = Path('models') / modelName
        if localFile.exists():
            return localFile
        
        return Path(cfg['MODELS_FOLDER']) / modelName


def IsModelFileExists(cfg: dict, var: dict, lang = 'ru') -> bool:
    return GetModelPath(cfg, var, lang).exists()


def PreloadModel(cfg: dict, var: dict, lang = 'ru'):
    modelPath = GetModelPath(cfg, var, lang)
    local_file = str(modelPath)

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file(var['languages'][lang].url, local_file)

    if (".pt" == modelPath.suffix):
        var['languages'][lang].extra['model'] = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        var['languages'][lang].extra['model'].to(var['device'])

    symb = var['languages'][lang].extra['model'].symbols
    var['languages'][lang].extra['symbols'] = re.compile(f"[{symb}]", re.IGNORECASE)


def GetModel(cfg: dict, var: dict, lang = 'ru'):
    if (lang in var['languages']) and ('model' in var['languages'][lang].extra) and (var['languages'][lang].extra['model'] is None):
        PreloadModel(cfg, var, lang)
    return var['languages'][lang].extra['model']


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


def GetSymbols(cfg: dict, var: dict, lang = 'ru'):
    if (lang in var['languages']) and ('model' in var['languages'][lang].extra) and (var['languages'][lang].extra['model'] is None):
        PreloadModel(cfg, var, lang)
    if (lang in var['languages']) and ('symbols' in var['languages'][lang].extra):
        return var['languages'][lang].extra['symbols']
    return ''


def GetSupportedAudioFormats(cfg: dict, var: dict):
    all_encoders = dxaudio.get_supported_encoders(cfg)
    supported = []
    for format, encoder in var['formats'].items():
        if encoder in all_encoders:
            supported.append(format)
    return supported


def IsCorrectPhrase(cfg: dict, var: dict, lang = 'ru', text = ''):
    symbols = GetSymbols(cfg, var, lang)
    if symbols:
        if re.search(symbols, text):
            return True
    return True


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


def PreConvertBookForTTS(file: Path, var: dict):
    var['gen'].mkdir(parents=True, exist_ok=True)
    if var['genjson'].exists():
        var['genjson'].unlink()

    info, cover = book.ParseBook(file, full=True)

    with open(str(var['genjson']), 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    file.unlink()
    return info, cover


def GeneratePause(var, timeMs = 300, name = "pause.wav"):
    extra = var['languages']['ru'].extra
    extra['model'].save_wav(ssml_text=f'<speak><break time="{timeMs}ms"/></speak>',
                speaker=extra['default'],
                sample_rate=var['sample_rate'],
                audio_path=str(var['genwav'] / name))


def ProcessSentence(lang, number, sentence, cfg, var):
    wavFile = var['genwav'] / f"{number}.wav"
    speaker = var['settings']['silero'][lang]['voice']
    return SayText(wavFile, lang, speaker, sentence, cfg, var)


def SayText(wavFile, lang, speaker, text, cfg, var):
    if IsCorrectPhrase(cfg, var, lang, text) and (not wavFile.exists()):
        # Generate
        # print(text)
        try:
            GetModel(cfg, var, lang).save_wav(text=text,
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



def ConvertBook(file: Path, info: dict, coverBytes, outputDirStr: str, dirFormat: str, proc: dict, cfg: dict, var:dict):
    dxfs.CreateDirectory(var['tmp'], var['gen'])
    dxfs.CreateDirectory(var['tmp'], var['genwav'])
    dxfs.CreateDirectory(var['tmp'], var['genout'])
    proc['status'] = 'process'

    codec = var['settings']['app']['codec']
    bitrate = var['settings']['app']['bitrate']
    encoder = var['formats'][codec]

    accentor = var['accentor']

    if info is None:
        info = json.loads(file.read_text(encoding='utf-8'))
        # info, coverBytes = book.ParseBook(file, full = True)

    proc['bookName'] = book.BookName(info, includeAuthor=True)
    lang = dxnormalizer.unify_lang(info['lang']) if ('lang' in info) else 'ru'

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

    jingles = getJingles(var)

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

    GeneratePause(var, 300, "pause.wav")
    GeneratePause(var, 500, "pause-long.wav")

    for section in info['sections']:
        sectionCount += 1
        sectionWavs = []    
        rawSectionTitle = section['title']
        sectionTitle = dxnormalizer.normalize(rawSectionTitle, lang)
        sectionTitle = accentor(sectionTitle) if 'ru' == lang else sectionTitle
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
                accentedText = accentor(s) if 'ru' == lang else s
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
                
                dxaudio.concatenate_wav_files(var['genwav'], sectionWavs, sectionWavFile)
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

        dxaudio.concatenate_wav_files(var['genout'], chapterWavs, bookWavFile)
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
     
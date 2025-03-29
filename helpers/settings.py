import os, json
from pathlib import Path


def check_sub_dict(d: dict, key: str):
    if not key in d:
        d[key] = {}


def check_sub_cat_dict(d: dict, cat: str, key: str):
    if not cat in d:
        d[cat] = {}
    if not key in d[cat]:
        d[cat][key] = {}


def in_dict(d: dict, cat: str, key: str):
    return cat in d and key in d[cat] and d[cat][key]


def in_cat_dict(d: dict, cat: str, sub: str, key: str):
    return (cat in d) and (sub in d[cat]) and (key in d[cat][sub]) and d[cat][sub][key] 


def set_if_none(d: dict, cat: str, key: str, value):
    if not in_dict(d, cat, key):
        d[cat][key] = value


def set_if_cat_none(d: dict, cat: str, sub: str, key: str, value):
    if not in_cat_dict(d, cat, sub, key):
        d[cat][sub][key] = value


def LoadOrDefault(cfg: dict, var: dict):
    s = {}

    settingsPath = Path(cfg['SETTINGS_FILE'])
    if settingsPath.exists():
        s = json.loads(settingsPath.read_text(encoding='utf-8'))

    outputFolder = cfg['OUTPUT_FOLDER'] if ('OUTPUT_FOLDER' in cfg) else 'AudioBooks'
    dirs = cfg['DIRECTORIES_FORMAT'] if ('DIRECTORIES_FORMAT' in cfg) else 'single'
    codec = cfg['AUDIO_CODEC'] if ('AUDIO_CODEC' in cfg) else 'mp3'
    processor = cfg['TORCH_DEVICE'] if ('TORCH_DEVICE' in cfg) else 'cpu'

    check_sub_dict(s, 'app')
    set_if_none(s, 'app', 'lang', '')
    set_if_none(s, 'app', 'output', outputFolder)
    set_if_none(s, 'app', 'codec', codec)
    set_if_none(s, 'app', 'dirs', dirs)
    set_if_none(s, 'app', 'processor', processor)

    num_threads = os.cpu_count() if ('cpu' == s['app']['processor']) else -1
    if ('TORCH_NUM_THREADS' in cfg) and int(cfg['TORCH_NUM_THREADS']) > 0:
        num_threads = cfg['TORCH_NUM_THREADS']
    set_if_none(s, 'app', 'threads', num_threads)


    for lang in var['languages']:
        check_sub_cat_dict(s, 'silero', lang)
        set_if_cat_none(s, 'silero', lang, 'voice', var[lang]['default'])

    return s



def Save(cfg: dict, settings: dict):
    with open(cfg['SETTINGS_FILE'], 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
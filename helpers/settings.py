import os, json, torch
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

    if 'SETTINGS_FILE' in cfg:
        settingsPath = Path(cfg['SETTINGS_FILE'])
        if settingsPath.exists():
            s = json.loads(settingsPath.read_text(encoding='utf-8'))

    outputFolder = cfg['OUTPUT_FOLDER'] if ('OUTPUT_FOLDER' in cfg) else 'AudioBooks'
    dirs = cfg['DIRECTORIES_FORMAT'] if ('DIRECTORIES_FORMAT' in cfg) else 'single'
    codec = cfg['AUDIO_CODEC'] if ('AUDIO_CODEC' in cfg) else 'mp3'
    defaultProcessor = 'cuda' if torch.cuda.is_available() else 'cpu'
    processor = cfg['TORCH_DEVICE'] if ('TORCH_DEVICE' in cfg) else defaultProcessor

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


def deep_compare_and_update(dict1, dict2):
    """
    Recursively compares dict1 with dict2 and overwrites values in dict1 
    where they exist in dict2 at the same path.
    
    Args:
        dict1 (dict): The dictionary to update
        dict2 (dict): The dictionary containing new values
    
    Returns:
        dict: The modified dict1
    """
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(value, dict) and isinstance(dict1[key], dict):
                # Recursively handle nested dictionaries
                deep_compare_and_update(dict1[key], value)
            else:
                # Overwrite if same path exists
                dict1[key] = value
        # else:
            # Add new key if not in dict1
            # dict1[key] = value
            
    return dict1

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

    if 'SETTINGS_FILE' in cfg:
        settingsPath = Path(cfg['SETTINGS_FILE'])
        if settingsPath.exists():
            s = json.loads(settingsPath.read_text(encoding='utf-8'))

    outputFolder = cfg['OUTPUT_FOLDER'] if ('OUTPUT_FOLDER' in cfg) else 'AudioBooks'
    dirs = cfg['DIRECTORIES_FORMAT'] if ('DIRECTORIES_FORMAT' in cfg) else 'single'
    codec = cfg['AUDIO_CODEC'] if ('AUDIO_CODEC' in cfg) else 'mp3'
    bitrate = int(cfg['AUDIO_BITRATE']) if ('AUDIO_BITRATE' in cfg) else 64

    check_sub_dict(s, 'app')
    set_if_none(s, 'app', 'lang', '')
    set_if_none(s, 'app', 'output', outputFolder)
    set_if_none(s, 'app', 'codec', codec)
    set_if_none(s, 'app', 'bitrate', bitrate)
    set_if_none(s, 'app', 'dirs', dirs)

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


def get_system_info_str(var: dict):
    s = ""

    try:
        # OS Information
        import platform
        s += f"Operating System: {platform.system()} {platform.release()}\n"
        s += f"OS Version: {platform.version()}\n"
        s += f"Architecture: {platform.machine()}\n"
        s += f"Hostname: {platform.node()}\n"
        s += f"Processor: {platform.processor()}\n"
    except:
        pass
    
    try:
        # Memory Information
        import psutil
        memory = psutil.virtual_memory()
        s += f"\nTotal RAM: {memory.total / (1024**3):.2f} GB\n"
        s += f"Available RAM: {memory.available / (1024**3):.2f} GB\n"
        s += f"Used RAM: {memory.used / (1024**3):.2f} GB\n"
        s += f"RAM Usage: {memory.percent}%\n"
        
        # Current Process Information
        current_process = psutil.Process(os.getpid())
        s += f"\nCurrent Process: {current_process.name()}\n"
        s += f"Process ID: {current_process.pid}\n"
        s += f"CPU Time (User): {current_process.cpu_times().user:.2f}s\n"
        s += f"CPU Time (System): {current_process.cpu_times().system:.2f}s\n"
        s += f"Total CPU Time: {sum(current_process.cpu_times())}s\n"
        s += f"Memory Usage: {current_process.memory_info().rss / (1024**2):.2f} MB\n"
        
        # Total System CPU Usage
        s += f"\nTotal CPU Usage: {psutil.cpu_percent(interval=1)}%\n"
        s += f"Number of CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical\n"
    except:
        pass
    
    # Check for CUDA availability
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        s += f"\nCUDA Available: {cuda_available}\n"
        if cuda_available:
            s += f"CUDA Device Count: {torch.cuda.device_count()}\n"
            s += f"CUDA Current Device: {torch.cuda.current_device()}\n"
            s += f"CUDA Device Name: {torch.cuda.get_device_name()}\n"
            s += f"CUDA Memory - Total: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB\n"
            s += f"CUDA Memory - Allocated: {torch.cuda.memory_allocated() / (1024**2):.2f} MB\n"
            s += f"CUDA Memory - Cached: {torch.cuda.memory_reserved() / (1024**2):.2f} MB\n"

        if ('cuda' in var['warning']) and var['warning']['cuda']:
            s += "\n" + var['warning']['cuda']
    except ImportError:
        s += "\nCUDA Check: PyTorch not installed - Cannot verify CUDA availability\n"
    
    return s

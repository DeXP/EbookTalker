import json, argparse
from pathlib import Path

default_json_en = 'static/i18n/en.json'
default_json_ru = 'static/i18n/ru.json'

parser = argparse.ArgumentParser(description='Generates Version info file for bundling with PyInstaller')
parser.add_argument('-v', '--version', help='Version number. Example: 0.7.9')
parser.add_argument('-o', '--output', help='Output VersionInfo file')
parser.add_argument('-e', '--en', default=default_json_en, help=f'English translation JSON file. Example: {default_json_en}')
parser.add_argument('-r', '--ru', default=default_json_ru, help=f'Russian translation JSON file. Example: {default_json_ru}')
parser.add_argument('-c', '--company', default='DeXPeriX - https://dexp.in', help='CompanyName')
parser.add_argument('-x', '--exeName', default='EbookTalker.exe', help='Original executable file name. Example: EbookTalker.exe')


args = parser.parse_args()

if not (args.version and args.output):
    print("Please provide required arguments. Run script with --help argument to see more")
else:
    en = json.loads(Path(args.en).read_text(encoding='utf8'))
    ru = json.loads(Path(args.ru).read_text(encoding='utf8'))

    version = args.version

    while version.count('.') < 3:
        version += '.0'

    comma_version = version.replace('.', ',')

    content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# https://learn.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource

VSVersionInfo(
ffi=FixedFileInfo(
    filevers=({comma_version}),
    prodvers=({comma_version}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
),
kids=[
    StringFileInfo(
    [
        StringTable(
          '040904b0',
          [
            StringStruct('CompanyName', '{args.company}'),
            StringStruct('FileDescription', '{en["appDescription"]}'),
            StringStruct('FileVersion', '{args.version}'),
            StringStruct('InternalName', '{en["appTitle"]}'),
            StringStruct('LegalCopyright', '{en["LegalCopyright"]}'),
            StringStruct('OriginalFilename', '{args.exeName}'),
            StringStruct('ProductName', '{en["appTitle"]}'),
            StringStruct('ProductVersion', '{args.version}')
          ]
        ),
        StringTable(
          '041904b0',
          [
            StringStruct('CompanyName', '{args.company}'),
            StringStruct('FileDescription', '{ru["appDescription"]}'),
            StringStruct('FileVersion', '{args.version}'),
            StringStruct('InternalName', '{ru["appTitle"]}'),
            StringStruct('LegalCopyright', '{ru["LegalCopyright"]}'),
            StringStruct('OriginalFilename', '{args.exeName}'),
            StringStruct('ProductName', '{ru["appTitle"]}'),
            StringStruct('ProductVersion', '{args.version}')
          ]
        )
    ]
    ),
    VarFileInfo([
      VarStruct('Translation', [1033, 1200]),
      VarStruct('Translation', [1049, 1200])
    ])
]
)'''
    # print(content)
    Path(args.output).write_text(content, encoding='utf8')
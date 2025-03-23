set /p Version=<.\static\version.txt
python .\helpers\generate-version-file.py -v %Version% -o .\data\tmp\versionInfo.rc

pyinstaller --name EbookTalker --noconfirm --noupx --onedir --windowed --distpath "..\EbookTalker-Win64" --icon ".\static\favicon.ico" --splash ".\static\book.png" --add-data "C:\Python313\Lib\site-packages\transliterate;transliterate" --version-file .\data\tmp\versionInfo.rc .\desktop.py

set /p Version=<.\static\version.txt
python .\helpers\generate-version-file.py -v %Version% -o .\data\tmp\versionInfo.rc

pyinstaller --name EbookTalker --noconfirm --noupx --onedir --windowed --distpath "..\EbookTalker-Win64" --icon ".\static\favicon.ico" --splash ".\static\splash.png" --add-data "silero_stress;silero_stress" --version-file .\data\tmp\versionInfo.rc .\desktop.py

xcopy "static\i18n" "..\EbookTalker-Win64\static\i18n" /i /s
xcopy "default.cfg" "..\EbookTalker-Win64\default.cfg" /y
move /Y "..\EbookTalker-Win64\EbookTalker\EbookTalker.exe" "..\EbookTalker-Win64\EbookTalker.exe"
rd /S /Q "..\EbookTalker-Win64\_internal"
move /Y "..\EbookTalker-Win64\EbookTalker\_internal" "..\EbookTalker-Win64\_internal"
rd /S /Q "..\EbookTalker-Win64\EbookTalker\"

IF EXIST "..\EbookTalker-Win64.zip" DEL /F "..\EbookTalker-Win64.zip"

; EbookTalker Installer (x64, localized, custom icon)
; Pass: -DVERSION=... -DBIGVERSION=... -DSOURCE_DIR=... -DOUT=... -DCOPYRIGHT=...
;       -DAPP_NAME_EN="EbookTalker" -DAPP_NAME_RU="Электронная книга"
;       -DDESCRIPTION_EN="Text-to-speech ebook reader" -DDESCRIPTION_RU="Программа для чтения электронных книг с озвучкой"

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"        ; ← Required for ${If}

!insertmacro GetSize

; === Validate required defines ===
!ifndef VERSION
  !error "VERSION must be defined"
!endif
!ifndef BIGVERSION
  !error "BIGVERSION must be defined"
!endif
!ifndef SOURCE_DIR
  !error "SOURCE_DIR must be defined"
!endif
!ifndef OUT
  !error "OUT must be defined"
!endif
!ifndef COPYRIGHT
  !error "COPYRIGHT must be defined"
!endif
!ifndef APP_NAME_EN
  !error "APP_NAME_EN must be defined"
!endif
!ifndef APP_NAME_RU
  !error "APP_NAME_RU must be defined"
!endif
!ifndef DESCRIPTION_EN
  !error "DESCRIPTION_EN must be defined"
!endif
!ifndef DESCRIPTION_RU
  !error "DESCRIPTION_RU must be defined"
!endif

!define COMPANY "DeXPeriX"
!define PACKAGE_ID "DeXPeriX.EbookTalker"
!define ICON_PATH "${SOURCE_DIR}\static\favicon.ico"

Name "EbookTalker"
OutFile "${OUT}"
InstallDir "$PROGRAMFILES64\EbookTalker"
RequestExecutionLevel admin
CRCCheck on

; === Maximum compression ===
SetCompressor /SOLID lzma
SetCompressorDictSize 64    ; 64 MB dictionary (max for LZMA in NSIS)

; === Custom icon ===
!define MUI_ICON "${ICON_PATH}"
!define MUI_UNICON "${ICON_PATH}"

; === Block 32-bit Windows ===
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "EbookTalker requires a 64-bit version of Windows."
    Abort
  ${EndIf}
FunctionEnd

; === EXE version info (English only) ===
VIProductVersion "${BIGVERSION}"
VIFileVersion "${BIGVERSION}"
VIAddVersionKey "ProductName" "EbookTalker"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "FileDescription" "${DESCRIPTION_EN}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "${COPYRIGHT}"

; === UI ===
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Russian"

; === Helper: Get localized strings based on UI language ===
Var localizedAppName
Var localizedDescription

Function SetLocalizedStrings
  ; Default to English
  StrCpy $localizedAppName "${APP_NAME_EN}"
  StrCpy $localizedDescription "${DESCRIPTION_EN}"

  ; Check if Russian language is active
  ${If} $LANGUAGE == ${LANG_RUSSIAN}
    StrCpy $localizedAppName "${APP_NAME_RU}"
    StrCpy $localizedDescription "${DESCRIPTION_RU}"
  ${EndIf}
FunctionEnd

; === Installer Section ===
Section "Main"
  SetRegView 64

  ; Initialize localized strings
  Call SetLocalizedStrings

  SetOutPath "$INSTDIR"
  File /r "${SOURCE_DIR}\*"

  ; Shortcuts with custom icon
  CreateShortCut "$DESKTOP\EbookTalker.lnk" "$INSTDIR\EbookTalker.exe" "" "${ICON_PATH}" 0
  CreateShortCut "$SMPrograms\EbookTalker.lnk" "$INSTDIR\EbookTalker.exe" "" "${ICON_PATH}" 0

  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Write localized uninstall entry
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "DisplayName" "$localizedAppName"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "Publisher" "${COMPANY}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "DisplayIcon" '"$INSTDIR\EbookTalker.exe",0'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "HelpLink" "https://github.com/DeXPeriX/EbookTalker"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "URLInfoAbout" "https://github.com/DeXPeriX/EbookTalker"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "NoRepair" 1

  ; EstimatedSize
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntOp $0 $0 / 1024
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}" "EstimatedSize" "$0"
SectionEnd

; === Uninstaller ===
Section "Uninstall"
  SetRegView 64
  Delete "$DESKTOP\EbookTalker.lnk"
  Delete "$SMPrograms\EbookTalker.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PACKAGE_ID}"
  DeleteRegKey HKCU "Software\${COMPANY}\EbookTalker"
SectionEnd
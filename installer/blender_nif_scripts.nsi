;
; Blender NIF Scripts Self-Installer for Windows
; (NSIS - http://nsis.sourceforge.net)
;

!include "MUI.nsh"

!define VERSION "1.2"

Name "Blender NIF Scripts ${VERSION}"
var BLENDERHOME

; define installer pages
!define MUI_ABORTWARNING

!define MUI_WELCOMEPAGE_TEXT  "This wizard will guide you through the installation of the Blender NIF Scripts.\r\n\r\nIt is recommended that you close all other applications.\r\n\r\nNote to Win2k/XP users: you require administrator privileges to install the Blender NIF Scripts successfully."
!insertmacro MUI_PAGE_WELCOME

!insertmacro MUI_PAGE_LICENSE Copyright.txt

!define MUI_DIRECTORYPAGE_TEXT_TOP "$BLENDERHOME\.blender\scripts\ has been detected as your Blender User Data directory. The Python scripts will be installed there.\r\n\r\nUse the field below to specify the folder where you want the documentation files to be copied to. To specify a different folder, type a new name or use the Browse button to select an existing folder."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Documentation Folder"
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.html"
!define MUI_FINISHPAGE_LINK "Visit us at http://niftools.sourceforge.net/"
!define MUI_FINISHPAGE_LINK_LOCATION "http://niftools.sourceforge.net/"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;--------------------------------
; Languages
 
!insertmacro MUI_LANGUAGE "English"
    
;--------------------------------
;Language Strings

;Description
LangString DESC_SecCopyUI ${LANG_ENGLISH} "Copy all required files to the application folder."

;--------------------------------
; Data

OutFile "blender_nif_scripts_${VERSION}-windows.exe"
InstallDir "$PROGRAMFILES\NifTools\Blender NIF Scripts"
BrandingText "http://niftools.sourceforge.net/"

;--------------------------------
; Functions

Function .onInit
  ; get Blender scripts dir

  ; check if Blender is installed
  ClearErrors
  ReadRegStr $BLENDERHOME HKLM SOFTWARE\BlenderFoundation "Install_Dir"
  IfErrors 0 +3

     ; no key, that means that Blender is not installed
     MessageBox MB_OK "Install Blender first. Get it from http://www.blender.org/"
     Abort ; causes installer to quit

  ; first try Blender's global install dir
  IfFileExists "$BLENDERHOME\.blender\scripts\*.*" end app_data

  ; now try Blender's application data directory
  app_data:
    StrCpy $BLENDERHOME "$PROFILE\Application Data\Blender Foundation\Blender"
    IfFileExists "$BLENDERHOME\.blender\scripts\*.*" end home_data
  
  ; finally, try the %HOME% variable
  home_data:
    ReadEnvStr $BLENDERHOME "HOME"
    IfFileExists "$BLENDERHOME\.blender\scripts\*.*" end 0
  
    MessageBox MB_OK "Blender User Data directory not found. Cannot install scripts."
    Abort ; causes installer to quit

  end:
FunctionEnd

Section "Blender-NIF-Scripts-${VERSION} (required)" SecCopyUI
  SectionIn RO

  SetShellVarContext all

  ; Cleanup: remove old versions of the scripts
  ; NIFLA versions
  Delete "$BLENDERHOME\.blender\scripts\nif-export.py"
  Delete "$BLENDERHOME\.blender\scripts\nif_import_237.py"
  ; SourceForge versions
  Delete "$BLENDERHOME\.blender\scripts\nif4_export.py"
  Delete "$BLENDERHOME\.blender\scripts\nif4_import_237.py"
  Delete "$BLENDERHOME\.blender\scripts\nif4.py"
  Delete "$BLENDERHOME\.blender\scripts\nif4.pyc"
  ; Current version, bytecode
  Delete "$BLENDERHOME\.blender\scripts\niflib.pyc"

  ; Install scripts
  SetOutPath "$BLENDERHOME\.blender\scripts\"
  File ..\nif_export.py
  File ..\nif4_import_240.py
  File ..\..\niflib\niflib.py
  File ..\..\niflib\_niflib.dll

  SetShellVarContext all

  ; Install documentation files
  SetOutPath $INSTDIR
  File ..\README.html
  File ..\ChangeLog
  File Copyright.txt

  ; Install shortcuts
  SetOutPath $INSTDIR
  CreateDirectory "$SMPROGRAMS\NifTools\Blender NIF Scripts\"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Readme.lnk" "$INSTDIR\README.html"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Tutorial.lnk" "http://niftools.sourceforge.net/tutorial/blender/"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Support.lnk" "http://niftools.sourceforge.net/forum/viewforum.php?f=6"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Development.lnk" "http://niftools.sourceforge.net/forum/viewforum.php?f=13"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Copyright.lnk" "$INSTDIR\Copyright.txt"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\BlenderNIFScripts "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM SOFTWARE\BlenderNIFScripts "Data_Dir" "$BLENDERHOME"

  ; Write the uninstall keys & uninstaller for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlenderNIFScripts" "DisplayName" "Blender NIF Scripts (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlenderNIFScripts" "UninstallString" "$INSTDIR\uninstall.exe"
  SetOutPath $INSTDIR
  WriteUninstaller "uninstall.exe"
SectionEnd

Section "Uninstall"
  SetShellVarContext all

  ; recover Blender data dir, where scripts are installed
  ReadRegStr $BLENDERHOME HKLM SOFTWARE\BlenderNIFScripts "Data_Dir"
  
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlenderNIFScripts"
  DeleteRegKey HKLM "SOFTWARE\BlenderNIFScripts"

  ; remove script files
  Delete "$BLENDERHOME\.blender\scripts\nif_export.py"
  Delete "$BLENDERHOME\.blender\scripts\nif4_import_240.py"
  Delete "$BLENDERHOME\.blender\scripts\niflib.py"
  Delete "$BLENDERHOME\.blender\scripts\niflib.pyc"
  Delete "$BLENDERHOME\.blender\scripts\_niflib.dll"

  ; remove program files
  Delete "$INSTDIR\*.*"
  RMDir "$INSTDIR"

  ; remove links in start menu
  Delete "$SMPROGRAMS\NifTools\Blender NIF Scripts\*.*"
  RMDir "$SMPROGRAMS\NifTools\Blender NIF Scripts"
  RMDir "$SMPROGRAMS\NifTools" ; this will only delete if the directory is empty
SectionEnd

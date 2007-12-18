;
; Blender NIF Scripts Self-Installer for Windows
; (NifTools - http://niftools.sourceforge.net) 
; (NSIS - http://nsis.sourceforge.net)
;
; Copyright (c) 2005-2007, NIF File Format Library and Tools
; All rights reserved.
; 
; Redistribution and use in source and binary forms, with or without
; modification, are permitted provided that the following conditions are
; met:
; 
;     * Redistributions of source code must retain the above copyright
;       notice, this list of conditions and the following disclaimer.
;     * Redistributions in binary form must reproduce the above copyright
;       notice, this list of conditions and the following disclaimer in the
;       documentation ; and/or other materials provided with the
;       distribution.
;     * Neither the name of the NIF File Format Library and Tools project
;       nor the names of its contributors may be used to endorse or promote
;       products derived from this software without specific prior written
;       permission.
; 
; THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
; IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
; THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
; PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
; CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
; EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
; PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
; PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
; LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
; NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
; SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 

SetCompressor /SOLID lzma

!include "MUI.nsh"
!include "WordFunc.nsh"
!insertmacro VersionCompare

!define VERSION "2.2.5"
!define PYFFIVERSION "0.7.1"

Name "Blender NIF Scripts ${VERSION}"
Var BLENDERHOME    ; blender settings location
Var BLENDERSCRIPTS ; blender scripts location ($BLENDERHOME/.blender/scripts)
Var BLENDERINST    ; blender.exe location
Var PYTHONPATH
Var PYFFI

; define installer pages
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_NOAUTOCLOSE

!define MUI_WELCOMEPAGE_TEXT  "This wizard will guide you through the installation of the Blender NIF Scripts ${VERSION}.\r\n\r\nIt is recommended that you close all other applications, especially Blender.\r\n\r\nNote to Win2k/XP users: you require administrator privileges to install the Blender NIF Scripts successfully."
!insertmacro MUI_PAGE_WELCOME

!insertmacro MUI_PAGE_LICENSE Copyright.txt

!define MUI_DIRECTORYPAGE_TEXT_TOP "The field below specifies the folder where the Blender scripts files will be copied to. This directory has been detected by analyzing your Blender installation.$\r$\n$\r$\nFor your convenience, the installer will also remove any old versions of the Blender NIF Scripts from this folder (no other files will be deleted).$\r$\n$\r$\nUnless you really know what you are doing, you should leave the field below as it is."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Blender Scripts Folder"
!define MUI_DIRECTORYPAGE_VARIABLE $BLENDERSCRIPTS
!insertmacro MUI_PAGE_DIRECTORY

!define MUI_DIRECTORYPAGE_TEXT_TOP "Use the field below to specify the folder where you want the documentation files to be copied to. To specify a different folder, type a new name or use the Browse button to select an existing folder."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Documentation Folder"
!define MUI_DIRECTORYPAGE_VARIABLE $INSTDIR
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.html"
!define MUI_FINISHPAGE_RUN "$BLENDERINST\blender.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Run Blender"
!define MUI_FINISHPAGE_LINK "Visit us at http://niftools.sourceforge.net/"
!define MUI_FINISHPAGE_LINK_LOCATION "http://niftools.sourceforge.net/"
!insertmacro MUI_PAGE_FINISH

!define MUI_WELCOMEPAGE_TEXT  "This wizard will guide you through the uninstallation of the Blender NIF Scripts ${VERSION}.\r\n\r\nBefore starting the uninstallation, make sure Blender is not running.\r\n\r\nClick Next to continue."
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

OutFile "blender_nif_scripts-${VERSION}-windows.exe"
InstallDir "$PROGRAMFILES\NifTools\Blender NIF Scripts"
BrandingText "http://niftools.sourceforge.net/"
Icon inst.ico
UninstallIcon inst.ico ; TODO create uninstall icon
ShowInstDetails show
ShowUninstDetails show

;--------------------------------
; Functions

; taken from http://nsis.sourceforge.net/Open_link_in_new_browser_window
# uses $0
Function openLinkNewWindow
  Push $3 
  Push $2
  Push $1
  Push $0
  ReadRegStr $0 HKCR "http\shell\open\command" ""
# Get browser path
    DetailPrint $0
  StrCpy $2 '"'
  StrCpy $1 $0 1
  StrCmp $1 $2 +2 # if path is not enclosed in " look for space as final char
    StrCpy $2 ' '
  StrCpy $3 1
  loop:
    StrCpy $1 $0 1 $3
    DetailPrint $1
    StrCmp $1 $2 found
    StrCmp $1 "" found
    IntOp $3 $3 + 1
    Goto loop
 
  found:
    StrCpy $1 $0 $3
    StrCmp $2 " " +2
      StrCpy $1 '$1"'
 
  Pop $0
  Exec '$1 $0'
  Pop $1
  Pop $2
  Pop $3
FunctionEnd

Function .onInit
  ; check if user is admin
  ; call userInfo plugin to get user info.  The plugin puts the result in the stack
  userInfo::getAccountType

  ; pop the result from the stack into $0
  pop $0

  ; compare the result with the string "Admin" to see if the user is admin. If match, jump 3 lines down.
  strCmp $0 "Admin" +3
  
    ; if there is not a match, print message and return
    messageBox MB_OK "You require administrator privileges to install the Blender NIF Scripts successfully."
    Abort ; quit installer
   

  ; check if Blender is installed

  ClearErrors
  ReadRegStr $BLENDERHOME HKLM SOFTWARE\BlenderFoundation "Install_Dir"
  IfErrors 0 blender_check_end

     ; no key, that means that Blender is not installed
     MessageBox MB_OK "You will need to download Blender in order to run the Blender NIF Scripts. Pressing OK will take you to the Blender download page. Please download and run the Blender windows installer. When you are done, rerun the Blender NIF Scripts installer."
     StrCpy $0 "http://www.blender.org/download/get-blender/"
     Call openLinkNewWindow
     Abort ; causes installer to quit

blender_check_end:
  StrCpy $BLENDERINST $BLENDERHOME

  ; get Blender scripts dir

  ; first try Blender's global install dir
  StrCpy $BLENDERSCRIPTS "$BLENDERHOME\.blender\scripts"
  IfFileExists "$BLENDERSCRIPTS\*.*" blender_scripts_end 0

  ; now try Blender's application data directory
  StrCpy $BLENDERHOME "$PROFILE\Application Data\Blender Foundation\Blender"
  StrCpy $BLENDERSCRIPTS "$BLENDERHOME\.blender\scripts"
  IfFileExists "$BLENDERSCRIPTS\*.*" blender_scripts_end 0
  
  ; finally, try the %HOME% variable
  ReadEnvStr $BLENDERHOME "HOME"
  StrCpy $BLENDERSCRIPTS "$BLENDERHOME\.blender\scripts"
  IfFileExists "$BLENDERSCRIPTS\*.*" blender_scripts_end 0
  
    ; all failed!
    MessageBox MB_OK "Blender scripts directory directory not found. This is a bug. Please report to http://niftools.sourceforge.net/forum/"
    Abort ; causes installer to quit

blender_scripts_end:

  ; check if Python 2.5 is installed
  ClearErrors
  ReadRegStr $PYTHONPATH HKLM SOFTWARE\Python\PythonCore\2.5\InstallPath ""
  IfErrors 0 python_check_end
  ReadRegStr $PYTHONPATH HKCU SOFTWARE\Python\PythonCore\2.5\InstallPath ""
  IfErrors 0 python_check_end

     ; no key, that means that Python 2.5 is not installed
     MessageBox MB_OK "You will need to download Python 2.5 and PyFFI in order to run the Blender NIF Scripts. Pressing OK will take you to the Python and PyFFI download pages. Please download and run the Python windows installer, then download and run the PyFFI windows installer. When you are done, rerun the Blender NIF Scripts installer."
     StrCpy $0 "http://sourceforge.net/project/platformdownload.php?group_id=199269&sel_platform=3089"
     Call openLinkNewWindow
     StrCpy $0 "http://www.python.org/download/"
     Call openLinkNewWindow
     Abort ; causes installer to quit

python_check_end:

  ; check if PyFFI is installed (the bdist_wininst installer only creates an uninstaller registry key, so that's how we check)
  ClearErrors
  ReadRegStr $PYFFI HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PyFFI-py2.5 "DisplayName"
  IfErrors 0 pyffi_check_end
  ReadRegStr $PYFFI HKCU SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PyFFI-py2.5 "DisplayName"
  IfErrors 0 pyffi_check_end

    ; no key, that means that PyFFI is not installed
     MessageBox MB_OK "You will need to download PyFFI in order to run the Blender NIF Scripts. Pressing OK will take you to the PyFFI download page. Please download and run the PyFFI windows installer. When you are done, rerun the Blender NIF Scripts installer."
     StrCpy $0 "http://sourceforge.net/project/platformdownload.php?group_id=199269&sel_platform=3089"
     Call openLinkNewWindow
     Abort ; causes installer to quit

pyffi_check_end:

  ; check PyFFI version
  StrCpy $R0 $PYFFI "" 17 ; strip "Python 2.5 PyFFI-"
  ${VersionCompare} "$R0" "${PYFFIVERSION}" $R1
  IntCmp $R1 0 pyffi_vercheck_end ; installed version is as indicated
  IntCmp $R1 1 pyffi_vercheck_end ; installed version is more recent than as indicated

     MessageBox MB_OK "You will need a more recent version of PyFFI in order to run the Blender NIF Scripts. Pressing OK will take you to the PyFFI download page. Please download and run the PyFFI windows installer. When you are done, rerun the Blender NIF Scripts installer."
     StrCpy $0 "http://sourceforge.net/project/platformdownload.php?group_id=199269&sel_platform=3089"
     Call openLinkNewWindow
     Abort ; causes installer to quit

pyffi_vercheck_end:

FunctionEnd

Section
  SectionIn RO

  SetShellVarContext all

  ; Cleanup: remove old versions of the scripts
  ; NIFLA versions
  Delete "$BLENDERSCRIPTS\nif-export.py"
  Delete "$BLENDERSCRIPTS\nif_import_237.py"
  ; SourceForge versions
  Delete "$BLENDERSCRIPTS\nif4_export.py"
  Delete "$BLENDERSCRIPTS\nif4_import_237.py"
  Delete "$BLENDERSCRIPTS\nif4_import_240.py"
  Delete "$BLENDERSCRIPTS\nif4.py"
  Delete "$BLENDERSCRIPTS\nif4.pyc"
  ; old config files
  Delete "$BLENDERSCRIPTS\bpydata\nif4.ini"
  Delete "$BLENDERSCRIPTS\bpydata\config\nif_import.cfg"
  Delete "$BLENDERSCRIPTS\bpydata\config\nif_export.cfg"
  ; old nifImEx lib
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\__init__.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Config.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Defaults.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Read.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Write.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\__init__.pyc"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Config.pyc"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Defaults.pyc"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Read.pyc"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\Write.pyc"
  Delete "$BLENDERSCRIPTS\bpymodules\nifImEx\niftools_logo.png"
  RMDir "$BLENDERSCRIPTS\bpymodules\nifImEx"
  ; clutter from svn 2905 revisions
  Delete "$BLENDERSCRIPTS\nif_common.py"
  Delete "$BLENDERSCRIPTS\nif_common.pyc"

  ; Clean up registered script menu's, just to make sure they get updated
  Delete "$BLENDERSCRIPTS\..\Bpymenus"

  ; Install scripts
  SetOutPath $BLENDERSCRIPTS
  File ..\scripts\nif_export.py
  File ..\scripts\nif_import.py
  File ..\scripts\mesh_weightsquash.py
  File ..\scripts\mesh_hull.py
  ; Install libraries
  SetOutPath $BLENDERSCRIPTS\bpymodules
  File ..\scripts\bpymodules\nif_common.py
  File ..\scripts\bpymodules\nif_test.py

  ; Install documentation files
  SetOutPath $INSTDIR
  File ..\README.html
  File /oname=ChangeLog.txt ..\ChangeLog
  File Copyright.txt

  ; Remove old shortcuts
  Delete "$SMPROGRAMS\NifTools\Blender NIF Scripts\*.lnk"

  ; Install shortcuts
  CreateDirectory "$SMPROGRAMS\NifTools\Blender NIF Scripts\"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Readme.lnk" "$INSTDIR\README.html"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\ChangeLog.lnk" "$INSTDIR\ChangeLog.txt"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Documentation.lnk" "http://niftools.sourceforge.net/wiki/Blender"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Bug Reports.lnk" "http://sourceforge.net/tracker/?group_id=149157&atid=776343"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Feature Requests.lnk" "http://sourceforge.net/tracker/?group_id=149157&atid=776346"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Forum.lnk" "http://niftools.sourceforge.net/forum/"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Copyright.lnk" "$INSTDIR\Copyright.txt"
  CreateShortCut "$SMPROGRAMS\NifTools\Blender NIF Scripts\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\BlenderNIFScripts "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM SOFTWARE\BlenderNIFScripts "Data_Dir" "$BLENDERSCRIPTS"

  ; Write the uninstall keys & uninstaller for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlenderNIFScripts" "DisplayName" "Blender NIF Scripts (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlenderNIFScripts" "UninstallString" "$INSTDIR\uninstall.exe"
  SetOutPath $INSTDIR
  WriteUninstaller "uninstall.exe"
SectionEnd

Section "Uninstall"
  SetShellVarContext all
  SetAutoClose false

  ; recover Blender data dir, where scripts are installed
  ReadRegStr $BLENDERSCRIPTS HKLM SOFTWARE\BlenderNIFScripts "Data_Dir"

  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlenderNIFScripts"
  DeleteRegKey HKLM "SOFTWARE\BlenderNIFScripts"

  ; remove script files
  Delete "$BLENDERSCRIPTS\nif_export.py"
  Delete "$BLENDERSCRIPTS\nif_import.py"
  Delete "$BLENDERSCRIPTS\mesh_weightsquash.py"
  Delete "$BLENDERSCRIPTS\mesh_hull.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nif_common.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nif_common.pyc"
  Delete "$BLENDERSCRIPTS\bpymodules\nif_test.py"
  Delete "$BLENDERSCRIPTS\bpymodules\nif_test.pyc"
  Delete "$BLENDERSCRIPTS\bpydata\config\nifscripts.cfg"

  ; remove program files and program directory
  Delete "$INSTDIR\*.*"
  RMDir "$INSTDIR"

  ; remove links in start menu
  Delete "$SMPROGRAMS\NifTools\Blender NIF Scripts\*.*"
  RMDir "$SMPROGRAMS\NifTools\Blender NIF Scripts"
  RMDir "$SMPROGRAMS\NifTools" ; this will only delete if the directory is empty
SectionEnd

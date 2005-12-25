;
; Blender NIF Scripts Self-Installer for Windows
; (NSIS - http://nsis.sourceforge.net)
;

!include "MUI.nsh"

!define VERSION "1.2"

Name "Blender NIF Scripts ${VERSION}"

; define installer pages
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TEXT  "This wizard will guide you through the installation of the Blender NIF Scripts.\r\n\r\nIt is recommended that you close all other applications before starting Setup.\r\n\r\nNote to Win2k/XP users: you may require administrator privileges to install the Blender NIF Scripts successfully."
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.html"
!define MUI_FINISHPAGE_LINK "Visit us at http://niftools.sourceforge.net/"
!define MUI_FINISHPAGE_LINK_LOCATION "http://niftools.sourceforge.net/"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE Copyright.txt
!insertmacro MUI_PAGE_DIRECTORY
Page custom DataLocation
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages
 
!insertmacro MUI_LANGUAGE "English"
    
;--------------------------------
;Language Strings

;Description
LangString DESC_SecCopyUI ${LANG_ENGLISH} "Copy all required files to the application folder."
LangString TEXT_IO_TITLE ${LANG_ENGLISH} "Specify Blender User Data Location."

;--------------------------------
;Data

Caption "Blender NIF Scripts ${VERSION} Installer"
OutFile "blender_nif_scripts-${VERSION}-windows.exe"
InstallDir "$PROGRAMFILES\NifTools\Blender NIF Scripts"
BrandingText "http://niftools.sourceforge.net/"
ComponentText "This will install the Blender NIF Scripts ${VERSION} on your computer."
DirText "Use the field below to specify the folder where you want the Blender NIF Scripts to be copied to. To specify a different folder, type a new name or use the Browse button to select an existing folder."

; GetWindowsVersion
;
; Based on Yazno's function, http://yazno.tripod.com/powerpimpit/
; Updated by Joost Verburg
;
; Returns on top of stack
;
; Windows Version (95, 98, ME, NT x.x, 2000, XP, 2003)
; or
; '' (Unknown Windows Version)
;
; Usage:
;   Call GetWindowsVersion
;   Pop $R0
;   ; at this point $R0 is "NT 4.0" or whatnot

Function GetWindowsVersion

  Push $R0
  Push $R1

  ReadRegStr $R0 HKLM \
  "SOFTWARE\Microsoft\Windows NT\CurrentVersion" CurrentVersion

  IfErrors 0 lbl_winnt
   
  ; we are not NT
  ReadRegStr $R0 HKLM \
  "SOFTWARE\Microsoft\Windows\CurrentVersion" VersionNumber
 
  StrCpy $R1 $R0 1
  StrCmp $R1 '4' 0 lbl_error
 
  StrCpy $R1 $R0 3
 
  StrCmp $R1 '4.0' lbl_win32_95
  StrCmp $R1 '4.9' lbl_win32_ME lbl_win32_98
 
  lbl_win32_95:
    StrCpy $R0 '95'
  Goto lbl_done
 
  lbl_win32_98:
    StrCpy $R0 '98'
  Goto lbl_done
 
  lbl_win32_ME:
    StrCpy $R0 'ME'
  Goto lbl_done
 
  lbl_winnt:

  StrCpy $R1 $R0 1
 
  StrCmp $R1 '3' lbl_winnt_x
  StrCmp $R1 '4' lbl_winnt_x
 
  StrCpy $R1 $R0 3
 
  StrCmp $R1 '5.0' lbl_winnt_2000
  StrCmp $R1 '5.1' lbl_winnt_XP
  StrCmp $R1 '5.2' lbl_winnt_2003 lbl_error
 
  lbl_winnt_x:
    StrCpy $R0 "NT $R0" 6
  Goto lbl_done
 
  lbl_winnt_2000:
    Strcpy $R0 '2000'
  Goto lbl_done
 
  lbl_winnt_XP:
    Strcpy $R0 'XP'
  Goto lbl_done
 
  lbl_winnt_2003:
    Strcpy $R0 '2003'
  Goto lbl_done
 
  lbl_error:
    Strcpy $R0 ''
  lbl_done:
 
  Pop $R1
  Exch $R0

FunctionEnd

Var BLENDERHOME
Var BLENDERINSTDIR
Var winversion

Function SetWinXPPath
  StrCpy $BLENDERHOME "$PROFILE\Application Data\Blender Foundation\Blender"
FunctionEnd

Function SetWin9xPath
  StrCpy $BLENDERHOME $BLENDERINSTDIR
FunctionEnd

Function .onInit
  ; get Windows version
  Call GetWindowsVersion
  Pop $R0
  Strcpy $winversion $R0
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "data.ini"

  ; get Blender install dir
  ReadRegStr $BLENDERINSTDIR HKLM SOFTWARE\BlenderFoundation "Install_Dir"
  IfErrors 0 NoAbort
     MessageBox MB_OK "Install Blender first. Get it from http://www.blender.org/"
     Abort ; causes installer to quit.
  NoAbort:
FunctionEnd

Var HWND
Var DLGITEM
Var is2KXP

Function DataLocation
  !insertmacro MUI_HEADER_TEXT "$(TEXT_IO_TITLE)" ""

  ; Set default choice
  !insertmacro MUI_INSTALLOPTIONS_WRITE "data.ini" "Field 3" "State" 1
  
  StrCpy $R1 $winversion 2
  StrCmp $R1 "NT" do_win2kxp
  StrCmp $winversion "2000" do_win2kxp
  StrCmp $winversion "XP" do_win2kxp
  StrCmp $winversion "2003" do_win2kxp
  
  ;else...
  Strcpy $is2KXP "false"

  Goto continue

  do_win2kXP:
    Strcpy $is2KXP "true"
    
  continue: 
  
  !insertmacro MUI_INSTALLOPTIONS_INITDIALOG "data.ini"
  Pop $HWND
  
  Strcmp $is2KXP "true" do_dlg
  
  ; Disable App Data option on Win9x
  
  GetDlgItem $DLGITEM $HWND 1201
  EnableWindow $DLGITEM 0  
  
  do_dlg:
  
    !insertmacro MUI_INSTALLOPTIONS_SHOW
    !insertmacro MUI_INSTALLOPTIONS_READ $R0 "data.ini" "Field 2" "State" ; App Dir
    Strcmp $R0 1 do_app_data
    !insertmacro MUI_INSTALLOPTIONS_READ $R0 "data.ini" "Field 3" "State" ; Inst Dir
    Strcmp $R0 1 do_inst_path
    !insertmacro MUI_INSTALLOPTIONS_READ $R0 "data.ini" "Field 4" "State" ; Home Dir
    Strcmp $R0 1 do_home_path
  
  Goto end
  
  do_app_data:
    Call SetWinXPPath
    Goto end
  do_home_path:
    ReadEnvStr $BLENDERHOME "HOME"
    Goto end
  do_inst_path:
    Call SetWin9xPath
  end:

  IfFileExists "$BLENDERHOME\.blender\scripts\*.*" +3 0
     MessageBox MB_OK "Invalid Blender User Data Location."
     Quit
FunctionEnd

Section "Blender-NIF-Scripts-${VERSION} (required)" SecCopyUI
  SectionIn RO
  
  ; install for all users
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
  
  ; Install the files
  SetOutPath $INSTDIR
  File ..\README.html
  File ..\ChangeLog
  File Copyright.txt

  SetOutPath "$BLENDERHOME\.blender\scripts\"
  File ..\nif_export.py
  File ..\nif4_import_240.py
  File ..\..\niflib\niflib.py
  File ..\..\niflib\_niflib.dll

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

UninstallText "This will uninstall the Blender NIF Scripts ${VERSION}. Hit next to continue."

Section "Uninstall"
  ; uninstall for all users
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
  RMDir "$BLENDERHOME\.blender\scripts" ; this will only delete if the directory is empty
  RMDir "$BLENDERHOME\.blender" ; this will only delete if the directory is empty

  ; remove program files
  Delete "$INSTDIR\*.*"
  RMDir "$INSTDIR"

  ; remove links in start menu
  Delete "$SMPROGRAMS\NifTools\Blender NIF Scripts\*.*"
  RMDir "$SMPROGRAMS\NifTools\Blender NIF Scripts"
  RMDir "$SMPROGRAMS\NifTools" ; this will only delete if the directory is empty
SectionEnd

;!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
;!insertmacro MUI_DESCRIPTION_TEXT ${SecCopyUI} $(DESC_SecCopyUI)
;!insertmacro MUI_FUNCTION_DESCRIPTION_END

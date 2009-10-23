set NAME=blender_nif_scripts
set VERSION=2.4.13
set FILES=scripts\import_nif.py scripts\export_nif.py scripts\mesh_niftools_weightsquash.py scripts\mesh_niftools_hull.py scripts\object_niftools_set_bone_priority.py scripts\object_niftools_save_bone_pose.py scripts\object_niftools_load_bone_pose.py scripts\bpymodules\nif_common.py scripts\bpymodules\nif_test.py ChangeLog README.html install.sh install.bat

del %NAME%-%VERSION%.*

"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip %NAME%-%VERSION%.zip %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -ttar %NAME%-%VERSION%.tar %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -tbzip2 %NAME%-%VERSION%.tar.bz2 %NAME%-%VERSION%.tar

del %NAME%-%VERSION%.tar

pause

del win-install\%NAME%-%VERSION%-windows.exe
if exist "%PROGRAMFILES%\NSIS\makensis.exe" "%PROGRAMFILES%\NSIS\makensis.exe" /v3 win-install\%NAME%.nsi
if exist "%PROGRAMFILES(x86)%\NSIS\makensis.exe" "%PROGRAMFILES(x86)%\NSIS\makensis.exe" /v3 win-install\%NAME%.nsi

pause

set NAME=blender_nif_scripts
set VERSION=2.3.9
set FILES=scripts\nif_import.py scripts\nif_export.py scripts\mesh_weightsquash.py scripts\mesh_hull.py scripts\object_setbonepriority.py scripts\object_savebonepose.py scripts\object_loadbonepose.py scripts\bpymodules\nif_common.py scripts\bpymodules\nif_test.py ChangeLog README.html install.sh install.bat

del %NAME%-%VERSION%.*

"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip %NAME%-%VERSION%.zip %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -ttar %NAME%-%VERSION%.tar %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -tbzip2 %NAME%-%VERSION%.tar.bz2 %NAME%-%VERSION%.tar

del %NAME%-%VERSION%.tar

pause

del win-install\%NAME%-%VERSION%-windows.exe
"%PROGRAMFILES%\NSIS\makensis.exe" /v3 win-install\%NAME%.nsi

pause

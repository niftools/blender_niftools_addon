set NAME=blender_nif_scripts
set VERSION=2.1.4
set FILES=scripts\nif_import.py scripts\nif_export.py scripts\mesh_weightsquash.py scripts\bpymodules\nifImEx\__init__.py scripts\bpymodules\nifImEx\Config.py  scripts\bpymodules\nifImEx\Defaults.py scripts\bpymodules\nifImEx\Read.py scripts\bpymodules\nifImEx\Write.py scripts\bpymodules\nifImEx\niftools_logo.png ChangeLog README.html install.sh

del %NAME%-%VERSION%.*

"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip %NAME%-%VERSION%.zip %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -ttar %NAME%-%VERSION%.tar %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -tbzip2 %NAME%-%VERSION%.tar.bz2 %NAME%-%VERSION%.tar

del %NAME%-%VERSION%.tar

pause

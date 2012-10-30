set /p VERSION=<../scripts/addons/io_scene_nif/VERSION
set NAME=blender_nif_plugin
set EXTRAFILES=AUTHORS.rst CHANGELOG.rst LICENSE.rst README.rst

pushd ..\scripts\addons
del %NAME%-%VERSION%.*
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip ..\..\install\%NAME%-%VERSION%.zip io_scene_nif -xr!__pycache__
popd

pushd ..
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip install\%NAME%-%VERSION%.zip %EXTRAFILES%
popd

pause

@echo off

set /p VERSION=<../scripts/addons/io_scene_nif/VERSION
set NAME=blender_nif_plugin
set EXTRAFILES=AUTHORS.rst CHANGELOG.rst LICENSE.rst README.rst

del %NAME%-%VERSION%.*

pushd ..\scripts\addons
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip ..\..\install\%NAME%-%VERSION%.zip -xr!__pycache__ io_scene_nif 
popd

pushd ..
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip install\%NAME%-%VERSION%.zip %EXTRAFILES%
popd

pause

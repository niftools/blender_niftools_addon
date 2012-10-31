@echo off

set /p VERSION=<../io_scene_nif/VERSION
set NAME=blender_nif_plugin

del %NAME%-%VERSION%.*

pushd ..
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip install\%NAME%-%VERSION%.zip -xr!__pycache__ io_scene_nif 
popd

pause

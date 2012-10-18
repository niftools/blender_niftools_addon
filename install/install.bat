@rem quick and dirty script to install the blender nif scripts
@rem to detect APPDATABLENDERADDONS, you can use https://github.com/neomonkeus/buildenv
@echo off

if "%APPDATABLENDERADDONS%" == "" goto pleasesetblenderaddons

echo.Installing to:
echo.%APPDATABLENDERADDONS%\io_scene_nif

rem remove old files
if exist "%APPDATABLENDERADDONS%\io_scene_nif" rmdir /s /q "%APPDATABLENDERADDONS%\io_scene_nif"

rem create root folder
mkdir "%APPDATABLENDERADDONS%\io_scene_nif"

rem add sub-folders
for %%A in (
collisionsys, armaturesys, texturesys, materialsys, ) do mkdir "%APPDATABLENDERADDONS%\io_scene_nif\%%A"

rem copy files from repository to blender addons folder
for %%A in (
__init__.py,
nif_common.py, nif_export.py, nif_import.py, nif_debug,
ui.py, properties.py, operators.py,
collisionsys, armaturesys, texturesys, materialsys, ) do (
  echo.	%%A
  copy "..\scripts\addons\io_scene_nif\%%A" "%APPDATABLENDERADDONS%\io_scene_nif\%%A"
)

goto end

:pleasesetblenderaddons
echo.Please set APPDATABLENDERADDONS to the folder where the blender addons reside, such as:
echo.
echo.  set APPDATABLENDERADDONS=%APPDATA%\Blender Foundation\Blender\2.63\scripts\addons
echo.
pause
goto end

:end

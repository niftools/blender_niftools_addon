@rem quick and dirty script to install the blender nif scripts
@rem to detect BLENDERADDONS, you can use https://github.com/neomonkeus/buildenv
@echo off

if "%BLENDERADDONS%" == "" goto pleasesetblenderaddons

echo.Installing to:
echo.%BLENDERADDONS%\io_scene_nif

rem remove old files
rmdir /s /q "%BLENDERADDONS%\io_scene_nif"

rem create root folder
mkdir "%BLENDERADDONS%\io_scene_nif"

rem add sub-folders
for %%A in ( 
collisionsys, armaturesys, texturesys, materialsys, ) do mkdir "%BLENDERADDONS%\io_scene_nif\%%A"

rem copy files from repository to blender addons folder
for %%A in ( 
__init__.py, 
nif_common.py, nif_export.py, nif_import.py, nif_debug,
ui.py, properties.py, operators.py, 
collisionsys, armaturesys, texturesys, materialsys, ) do (
  echo.	%%A
  copy "scripts\addons\io_scene_nif\%%A" "%BLENDERADDONS%\io_scene_nif\%%A"
)

goto end

:pleasesetblenderaddons
echo.Please set BLENDERADDONS to the folder where the blender addons reside, such as:
echo.
echo.  set BLENDERADDONS=C:\Program Files\Blender Foundation\Blender\2.62\scripts\addons
echo.
pause
goto end

:end

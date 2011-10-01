@rem quick and dirty linux shell script to install the scripts in a user's local blender dir
@echo off

if "%BLENDERADDONS%" == "" goto pleasesetblenderhome

echo.Installing in
echo.%BLENDERADDONS%\io_scene_nif
rem remove old files
rmdir /s /q "%BLENDERADDONS%\io_scene_nif"
rem copy files from repository to blender addons folder
for %%A in (io_scene_nif, ) do mkdir "%BLENDERADDONS%\%%A"
for %%A in (__init__.py, import_export_nif.py, export_nif.py, import_nif.py) do (
  copy "scripts\addons\io_scene_nif\%%A" "%BLENDERADDONS%\io_scene_nif"
)
goto end

:pleasesetblenderhome
echo.Please set BLENDERADDONS to the folder where blender.exe resides, such as:
echo.
echo.  set BLENDERADDONS=C:\Program Files\Blender Foundation\Blender\2.59\scripts\addons
echo.
pause
goto end

:end

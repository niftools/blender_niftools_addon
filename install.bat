@rem quick and dirty linux shell script to install the scripts in a user's local blender dir
@echo off

if "%BLENDERHOME%" == "" goto pleasesetblenderhome

echo.Installing in %BLENDERHOME%

if not exist "%BLENDERHOME%\blender.exe" (
echo.%BLENDERHOME%\blender.exe not found!
echo.
goto pleasesetblenderhome
)

set BLENDERADDONS=%BLENDERHOME%\2.59\scripts\addons

echo on

@echo Removing clutter
@for %%A in ("%BLENDERADDONS%\io_scene_nif\*.*") do if exist "%%A" del "%%A"

@echo Installing files
@for %%A in (io_scene_nif, ) do mkdir "%BLENDERADDONS%\%%A"
@for %%A in (__init__.py, import_export_nif.py, export_nif.py, import_nif.py) do copy "scripts\addons\io_scene_nif\%%A" "%BLENDERADDONS%\io_scene_nif"

@echo off

echo.
echo.Done!
echo.
goto end

:pleasesetblenderhome
echo.Please set BLENDERHOME to the folder where blender.exe resides, such as:
echo.
echo.  set BLENDERHOME="C:\Program Files\Blender Foundation\Blender"
echo.
pause
goto end

:end

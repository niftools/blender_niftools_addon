@rem quick and dirty script to install the blender nif scripts
@rem to detect APPDATABLENDERADDONS, you can use https://github.com/neomonkeus/buildenv
@echo off

if "%APPDATABLENDERADDONS%" == "" goto pleasesetblenderaddons

echo.Installing to:
echo.%APPDATABLENDERADDONS%\io_scene_nif

rem remove old files
if exist "%APPDATABLENDERADDONS%\io_scene_nif" rmdir /s /q "%APPDATABLENDERADDONS%\io_scene_nif"

rem create zip
makezip.bat

rem copy files from repository to blender addons folder
"%PROGRAMFILES%\7-Zip\7z.exe" x -o "%APPDATABLENDERADDONS%" "%NAME%-%VERSION%.zip"

goto end

:pleasesetblenderaddons
echo.Please set APPDATABLENDERADDONS to the folder where the blender addons reside, such as:
echo.
echo.  set APPDATABLENDERADDONS=%APPDATA%\Blender Foundation\Blender\2.63\scripts\addons
echo.
pause
goto end

:end

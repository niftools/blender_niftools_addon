@echo off

:: quick and dirty script to install the blender nif scripts
:: to detect APPDATABLENDERADDONS, you can use https://github.com/neomonkeus/buildenv

set DIR=%~dp0
:: remove trailing backslash
if %DIR:~-1%==\ set DIR=%DIR:~0,-1%
set ROOT=%DIR%\..
set /p VERSION=<%ROOT%\io_scene_nif\VERSION
set NAME=blender_nif_plugin

if "%APPDATABLENDERADDONS%" == "" goto pleasesetblenderaddons

echo.Installing to:
echo.%APPDATABLENDERADDONS%\io_scene_nif

rem remove old files
if exist "%APPDATABLENDERADDONS%\io_scene_nif" rmdir /s /q "%APPDATABLENDERADDONS%\io_scene_nif"

rem create zip
call "%DIR%\makezip.bat"

rem copy files from repository to blender addons folder
pushd "%APPDATABLENDERADDONS%"
"%PROGRAMFILES%\7-Zip\7z.exe" x "%DIR%\%NAME%-%VERSION%.zip"
popd

goto end

:pleasesetblenderaddons
echo.Please set APPDATABLENDERADDONS to the folder where the blender addons reside, such as:
echo.
echo.  set APPDATABLENDERADDONS=%APPDATA%\Blender Foundation\Blender\2.63\scripts\addons
echo.
pause
goto end

:end

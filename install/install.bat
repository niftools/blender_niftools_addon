@echo off

:: Script to install the blender nif scripts

set DIR=%~dps0
:: remove trailing backslash
if "%DIR:~-1%" == "\" set DIR="%DIR:~0,-1%"
set ROOT="%DIR%\.."
set /p VERSION=<%ROOT%\io_scene_nif\VERSION
set NAME=blender_nif_plugin

if "%BLENDER_ADDONS_DIR%" == "" if not exist "%BLENDER_ADDONS_DIR%" (
echo. "Update BLENDER_ADDONS_DIR to the folder where the blender addons reside, such as:"
echo. "set BLENDER_ADDONS_DIR=%APPDATA%\Blender Foundation\Blender\2.79\scripts\addons"
echo.
pause
goto end
)

echo "Blender addons directory : %BLENDER_ADDONS_DIR%"
echo. "Installing to: %BLENDER_ADDONS_DIR%\io_scene_nif"

:: create zip
echo. "Building artifact"
call "%DIR%\makezip.bat"

:: remove old files
echo.Removing old installation
if exist "%BLENDER_ADDONS_DIR%\io_scene_nif" rmdir /s /q "%BLENDER_ADDONS_DIR%\io_scene_nif"

:: copy files from repository to blender addons folder
powershell -executionpolicy bypass -Command "%DIR%\unzip.ps1" -source '%DIR%\%NAME%-%VERSION%.zip' -destination '%BLENDER_ADDONS_DIR%\io_scene_nif'

:end
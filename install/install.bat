@echo off

:: Script to install the blender nif scripts

set "DIR=%~dps0"
:: remove trailing backslash
if "%DIR:~-1%" == "\" set "DIR=%DIR:~0,-1%"
for %%I in ("%DIR%\..") do set "ROOT=%%~fI"
set "NAME=blender_niftools_addon"
set /p VERSION=<%ROOT%\io_scene_niftools\VERSION.txt
for /f %%i in ('git rev-parse --short HEAD') do set HASH=%%i
:: Use PowerShell to get current date in YYYY-MM-DD format independent of local format
for /f %%i in ('powershell -executionpolicy bypass -Command Get-Date -Format "yyyy-MM-dd"') do set DATE=%%i
set "ZIP_NAME=%NAME%-%VERSION%-%DATE%-%HASH%"

if "%BLENDER_ADDONS_DIR%" == "" if not exist "%BLENDER_ADDONS_DIR%" (
echo. "Update BLENDER_ADDONS_DIR to the folder where the blender addons reside, such as:"
echo. "set BLENDER_ADDONS_DIR=%APPDATA%\Blender Foundation\Blender\2.90\scripts\addons"
echo.
pause
goto end
)

echo "Blender addons directory : %BLENDER_ADDONS_DIR%"
echo. "Installing to: %BLENDER_ADDONS_DIR%\io_scene_niftools"

:: create zip
echo. "Building artifact"
call "%DIR%\makezip.bat"

:: remove old files
echo.Removing old installation
if exist "%BLENDER_ADDONS_DIR%\io_scene_niftools" rmdir /s /q "%BLENDER_ADDONS_DIR%\io_scene_niftools"

:: copy files from repository to blender addons folder
powershell -executionpolicy bypass -Command "%DIR%\unzip.ps1" -source '%DIR%\%ZIP_NAME%.zip' -destination '%BLENDER_ADDONS_DIR%'

:end
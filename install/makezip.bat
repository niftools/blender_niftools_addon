@echo off

set "DIR=%~dps0"
:: remove trailing backslash
if "%DIR:~-1%" == "\" (
    set "DIR=%DIR:~0,-1%"
)

for %%I in ("%DIR%\..") do set "ROOT=%%~fI"
set "NAME=blender_niftools_addon"
set /p VERSION=<%ROOT%\io_scene_nif\VERSION.txt
:: Abuse for loop to execute and store command output
for /f %%i in ('git rev-parse --short HEAD') do set HASH=%%i
for /f %%i in ('echo %date%') do set DATE=%%i
set "ZIP_NAME=%NAME%-%VERSION%-%DATE%-%HASH%"
set PYFFI_VERSION="2.2.4.dev3"
set DEPS="io_scene_nif\dependencies"
if exist "%DIR%\temp" rmdir /s /q "%DIR%\temp"

mkdir "%DIR%"\temp

pushd "%DIR%"\temp
mkdir io_scene_nif
xcopy /s "%ROOT%\io_scene_nif" io_scene_nif
mkdir "%DEPS%"

python -m pip install "PyFFI==%PYFFI_VERSION%" --target="%DEPS%"

xcopy "%ROOT%"\AUTHORS.rst io_scene_nif
xcopy "%ROOT%"\CHANGELOG.rst io_scene_nif
xcopy "%ROOT%"\LICENSE.rst io_scene_nif
xcopy "%ROOT%"\README.rst io_scene_nif
popd

powershell -executionpolicy bypass -Command "%DIR%\zip.ps1" -source "%DIR%\temp\io_scene_nif" -destination "%DIR%\%ZIP_NAME%.zip"
rmdir /s /q %DIR%\temp

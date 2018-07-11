@echo off

set DIR=%~dps0
:: remove trailing backslash
if %DIR:~-1%==\ set DIR=%DIR:~0,-1%
set ROOT=%DIR%\..
set /p VERSION=<%ROOT%\io_scene_nif\VERSION
set NAME=blender_nif_plugin
set DEPS=io_scene_nif\dependencies
if exist "%DIR%\temp" rmdir /s /q "%DIR%\temp"
pushd %ROOT%
%git% clean -xfd
%git% submodule foreach --recursive %git% clean -xfd
popd

mkdir %DIR%\temp

pushd %DIR%\temp
mkdir io_scene_nif
xcopy /s %ROOT%\io_scene_nif io_scene_nif
mkdir %DEPS%
mkdir %DEPS%\pyffi
xcopy /s %ROOT%\pyffi\pyffi %DEPS%\pyffi
xcopy %ROOT%\pyffi\*.rst %DEPS%\pyffi
rmdir /s /q %DEPS%\pyffi\formats\cgf
rmdir /s /q %DEPS%\pyffi\formats\dae
rmdir /s /q %DEPS%\pyffi\formats\psk
rmdir /s /q %DEPS%\pyffi\formats\rockstar
rmdir /s /q %DEPS%\pyffi\formats\tga
rmdir /s /q %DEPS%\pyffi\qskope
xcopy %ROOT%\AUTHORS.rst io_scene_nif
xcopy %ROOT%\CHANGELOG.rst io_scene_nif
xcopy %ROOT%\LICENSE.rst io_scene_nif
xcopy %ROOT%\README.rst io_scene_nif
popd

powershell -executionpolicy bypass -Command "%DIR%\zip.ps1" -source "%DIR%\temp\io_scene_nif" -destination "%DIR%\%NAME%-%VERSION%.zip"
rmdir /s /q %DIR%\temp

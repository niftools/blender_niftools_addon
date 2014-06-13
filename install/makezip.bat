@echo off

set DIR=%~dps0
:: remove trailing backslash
if %DIR:~-1%==\ set DIR=%DIR:~0,-1%
set ROOT=%DIR%\..
set /p VERSION=<%ROOT%\io_scene_nif\VERSION
set NAME=blender_nif_plugin

if "%SEVENZIPHOME%" == "" goto sevenzipnotfounderror

if exist "%DIR%\temp" rmdir /s /q "%DIR%\temp"
pushd %ROOT%
%git% clean -xfd
%git% submodule foreach --recursive %git% clean -xfd
popd

mkdir %DIR%\temp

pushd %DIR%\temp
mkdir io_scene_nif
xcopy /s %ROOT%\io_scene_nif io_scene_nif
mkdir io_scene_nif\modules
mkdir io_scene_nif\modules\pyffi
xcopy /s %ROOT%\pyffi\pyffi io_scene_nif\modules\pyffi
xcopy %ROOT%\pyffi\*.rst io_scene_nif\modules\pyffi
rmdir /s /q io_scene_nif\modules\pyffi\formats\cgf
rmdir /s /q io_scene_nif\modules\pyffi\formats\dae
rmdir /s /q io_scene_nif\modules\pyffi\formats\psk
rmdir /s /q io_scene_nif\modules\pyffi\formats\rockstar
rmdir /s /q io_scene_nif\modules\pyffi\formats\tga
rmdir /s /q io_scene_nif\modules\pyffi\qskope
xcopy %ROOT%\AUTHORS.rst io_scene_nif
xcopy %ROOT%\CHANGELOG.rst io_scene_nif
xcopy %ROOT%\LICENSE.rst io_scene_nif
xcopy %ROOT%\README.rst io_scene_nif
"%SEVENZIPHOME%\7z.exe" a -tzip "%DIR%\%NAME%-%VERSION%.zip" -xr!__pycache__ -xr!.git -xr!.project -xr!fileformat.dtd io_scene_nif
popd

rmdir /s /q %DIR%\temp

goto end

:sevenzipnotfounderror
echo.Please set SEVENZIPHOME to the folder where 7-zip is installed to, such as:
echo.
echo. set SEVENZIPHOME=%PROGRAMFILES%\7-Zip\
echo.
pause

:end

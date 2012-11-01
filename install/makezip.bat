@echo off

set /p VERSION=<../io_scene_nif/VERSION
set NAME=blender_nif_plugin

del %NAME%-%VERSION%.*

pushd ..
git clean -xfd
xcopy /s pyffi/pyffi io_scene_nif/pyffi
xcopy pyffi/*.rst io_scene_nif/pyffi
del /s /f /q io_scene_nif/pyffi/formats/cgf
del /s /f /q  io_scene_nif/pyffi/formats/dae
del /s /f /q  io_scene_nif/pyffi/formats/psk
del /s /f /q  io_scene_nif/pyffi/formats/rockstar
del /s /f /q  io_scene_nif/pyffi/formats/tga
del /s /f /q  io_scene_nif/pyffi/qskope
copy AUTHORS.rst io_scene_nif
copy CHANGELOG.rst io_scene_nif
copy LICENSE.rst io_scene_nif
copy README.rst io_scene_nif
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip install\%NAME%-%VERSION%.zip -xr!__pycache__ -xr!.git -xr!.project -xr!fileformat.dtd io_scene_nif
del /s /f /q io_scene_nif/pyffi
popd

pause

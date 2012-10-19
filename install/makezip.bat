git clean -xfd
install.bat

set /p VERSION=<../scripts/addons/io_scene_nif/VERSION
set NAME=blender_nif_plugin
set FILES=AUTHORS.rst CHANGELOG.rst LICENSE.rst README.rst install/install.sh install/install.bat scripts/  docs/_build/html/

rem update documentation
pushd ../docs
make clean
make html
popd

del %NAME%-%VERSION%.*
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip %NAME%-%VERSION%.zip %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -ttar %NAME%-%VERSION%.tar %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -tbzip2 %NAME%-%VERSION%.tar.bz2 %NAME%-%VERSION%.tar

del %NAME%-%VERSION%.tar

rem create windows installer
del %NAME%-%VERSION%-windows.exe
makensis.exe /v3 /DVERSION=%VERSION% %NAME%.nsi

pause

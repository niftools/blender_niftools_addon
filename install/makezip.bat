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

pushd ..
del %NAME%-%VERSION%.*
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip install/%NAME%-%VERSION%.zip %FILES%

pause

set VERSION=2.6.0.2
set NAME=blender_nif_plugin
set FILES= ../AUTHORS.rst ../CHANGELOG.rst ../LICENSE.rst ../README.rst install.sh install.bat ../scripts/ ../docs/_build/html/

pushd ../docs
make clean
make html
popd

del %NAME%-%VERSION%.*
"%PROGRAMFILES%\7-Zip\7z.exe" a -tzip %NAME%-%VERSION%.zip %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -ttar %NAME%-%VERSION%.tar %FILES%
"%PROGRAMFILES%\7-Zip\7z.exe" a -tbzip2 %NAME%-%VERSION%.tar.bz2 %NAME%-%VERSION%.tar

del %NAME%-%VERSION%.tar

pause

del %NAME%-%VERSION%-windows.exe

if exist "%PROGRAMFILES%\NSIS\makensis.exe" (
"%PROGRAMFILES%\NSIS\makensis.exe" /v3 %NAME%.nsi
goto end
)
if exist "%PROGRAMFILES(x86)%\NSIS\makensis.exe" (
"%PROGRAMFILES(x86)%\NSIS\makensis.exe" /v3 %NAME%.nsi
)

:end
pause

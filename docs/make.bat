@ECHO OFF

pushd %~dp0

if "%BLENDER_HOME%" == "" (
	echo.Please set BLENDER_HOME to the blender.exe folder
	goto end
)
set SPHINX_BUILD="%BLENDER_HOME%/blender.exe" --background --factory-startup --python blender-sphinx-build.py --
set SPHINX_API_BUILD="%BLENDER_HOME%/blender.exe" --background --factory-startup --python blender-sphinx-api-build.py --
set BUILD_DIR=_build

set CODE_API=../io_scene_niftools/
set CODE_DIR=development/api/submodules
set CODE_OPTS=%CODE_DIR% %CODE_API%

set TEST_API=../testframework/
set TEST_DIR=development/testframework/api/submodules
set TEST_OPTS=%TEST_DIR% %TEST_API%

set ALL_API_OPTS=%TEST_OPTS% %CODE_DIR%
set ALL_SPHINX_OPTS=-d %BUILD_DIR%/doctrees %SPHINXOPTS% .
set I18N_SPHINX_OPTS=%SPHINXOPTS% .
if NOT "%PAPER%" == "" (
	set ALL_SPHINX_OPTS=-D latex_paper_size=%PAPER% %ALL_SPHINX_OPTS%
	set I18N_SPHINX_OPTS=-D latex_paper_size=%PAPER% %I18N_SPHINX_OPTS%
)
set SOURCEDIR=.
set BUILDDIR=_build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd

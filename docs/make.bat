@ECHO OFF

:: Command file for Sphinx documentation

if "%BLENDER_HOME%" == "" (
	echo.Please set BLENDER_HOME to the blender.exe folder
	goto end
)
set SPHINX_BUILD="%BLENDER_HOME%/blender.exe" --background --factory-startup --python blender-sphinx-build.py --
set SPHINX_API_BUILD="%BLENDER_HOME%/blender.exe" --background --factory-startup --python blender-sphinx-api-build.py --
set BUILD_DIR=_build

set CODE_API=../io_scene_nif/
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

if "%1" == "" goto help

if "%1" == "help" (
	:help
	echo.Please use `make ^<target^>` where ^<target^> is one of
	echo.  clean      to clean your build directory
	echo.  html       to make standalone HTML files
	echo.  htmlclean  to clean your build directory and make standalone HTML files
	echo.  dirhtml    to make HTML files named index.html in directories
	echo.  singlehtml to make a single large HTML file
	echo.  pickle     to make pickle files
	echo.  json       to make JSON files
	echo.  htmlhelp   to make HTML files and a HTML help project
	echo.  qthelp     to make HTML files and a qthelp project
	echo.  devhelp    to make HTML files and a Devhelp project
	echo.  epub       to make an epub
	echo.  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter
	echo.  text       to make text files
	echo.  man        to make manual pages
	echo.  texinfo    to make Texinfo files
	echo.  gettext    to make PO message catalogs
	echo.  changes    to make an overview over all changed/added/deprecated items
	echo.  linkcheck  to check all external links for integrity
	echo.  doctest    to run all doctests embedded in the documentation if enabled
	goto end
)

if "%1" == "htmlfull" (
	call make.bat clean
	call make.bat gencodeapi
	call make.bat gentestapi
	call make.bat html
)

if "%1" == "clean" (
	for /d %%i in (%BUILD_DIR%\*) do rmdir /q /s %%i
	del /q /s %BUILD_DIR%\*
	del /q /s "%CODE_DIR%\*"
	del /q /s "%TEST_DIR%\*"
	goto end
)

if "%1" == "html" (
	%SPHINX_BUILD% -b html %ALL_SPHINX_OPTS% %BUILD_DIR%/html
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILD_DIR%/html.
	goto end
)

if "%1" == "gencodeapi" (
	echo.
	echo.Generating auto-docs from addon source api
	echo.
	%SPHINX_API_BUILD% -o %CODE_OPTS%
	if errorlevel 1 exit /b 1
	echo.Generated auto-docs
	goto end
)

if "%1" == "gentestapi" (
	echo.
	echo.Generating auto-docs for testframework api
	%SPHINX_API_BUILD% -o %TEST_OPTS%
	if errorlevel 1 exit /b 1
	echo.Generated auto-docs for testframework
	goto end
)

if "%1" == "dirhtml" (
	%SPHINX_BUILD% -b dirhtml %ALL_SPHINX_OPTS% %BUILD_DIR%/dirhtml
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILD_DIR%/dirhtml.
	goto end
)

if "%1" == "singlehtml" (
	%SPHINX_BUILD% -b singlehtml %ALL_SPHINX_OPTS% %BUILD_DIR%/singlehtml
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILD_DIR%/singlehtml.
	goto end
)

if "%1" == "pickle" (
	%SPHINX_BUILD% -b pickle %ALL_SPHINX_OPTS% %BUILD_DIR%/pickle
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can process the pickle files.
	goto end
)

if "%1" == "json" (
	%SPHINX_BUILD% -b json %ALL_SPHINX_OPTS% %BUILD_DIR%/json
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can process the JSON files.
	goto end
)

if "%1" == "htmlhelp" (
	%SPHINX_BUILD% -b htmlhelp %ALL_SPHINX_OPTS% %BUILD_DIR%/htmlhelp
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can run HTML Help Workshop with the .hhp project file in %BUILD_DIR%/htmlhelp.
	goto end
)

if "%1" == "qthelp" (
	%SPHINX_BUILD% -b qthelp %ALL_SPHINX_OPTS% %BUILD_DIR%/qthelp
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can run "qcollectiongenerator" with the .qhcp project file in %BUILD_DIR%/qthelp, like this:
	echo.^> qcollectiongenerator %BUILD_DIR%\qthelp\BlenderNIFScripts.qhcp
	echo.To view the help file:
	echo.^> assistant -collectionFile %BUILD_DIR%\qthelp\BlenderNIFScripts.ghc
	goto end
)

if "%1" == "devhelp" (
	%SPHINX_BUILD% -b devhelp %ALL_SPHINX_OPTS% %BUILD_DIR%/devhelp
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished.
	goto end
)

if "%1" == "epub" (
	%SPHINX_BUILD% -b epub %ALL_SPHINX_OPTS% %BUILD_DIR%/epub
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The epub file is in %BUILD_DIR%/epub.
	goto end
)

if "%1" == "latex" (
	%SPHINX_BUILD% -b latex %ALL_SPHINX_OPTS% %BUILD_DIR%/latex
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; the LaTeX files are in %BUILD_DIR%/latex.
	goto end
)

if "%1" == "text" (
	%SPHINX_BUILD% -b text %ALL_SPHINX_OPTS% %BUILD_DIR%/text
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The text files are in %BUILD_DIR%/text.
	goto end
)

if "%1" == "man" (
	%SPHINX_BUILD% -b man %ALL_SPHINX_OPTS% %BUILD_DIR%/man
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The manual pages are in %BUILD_DIR%/man.
	goto end
)

if "%1" == "texinfo" (
	%SPHINX_BUILD% -b texinfo %ALL_SPHINX_OPTS% %BUILD_DIR%/texinfo
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The Texinfo files are in %BUILD_DIR%/texinfo.
	goto end
)

if "%1" == "gettext" (
	%SPHINX_BUILD% -b gettext %I18N_SPHINX_OPTS% %BUILD_DIR%/locale
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The message catalogs are in %BUILD_DIR%/locale.
	goto end
)

if "%1" == "changes" (
	%SPHINX_BUILD% -b changes %ALL_SPHINX_OPTS% %BUILD_DIR%/changes
	if errorlevel 1 exit /b 1
	echo.
	echo.The overview file is in %BUILD_DIR%/changes.
	goto end
)

if "%1" == "linkcheck" (
	%SPHINX_BUILD% -b linkcheck %ALL_SPHINX_OPTS% %BUILD_DIR%/linkcheck
	if errorlevel 1 exit /b 1
	echo.
	echo.Link check complete; look for any errors in the above output or in %BUILD_DIR%/linkcheck/output.txt.
	goto end
)

if "%1" == "doctest" (
	%SPHINX_BUILD% -b doctest %ALL_SPHINX_OPTS% %BUILD_DIR%/doctest
	if errorlevel 1 exit /b 1
	echo.
	echo.Testing of doctests in the sources finished, look at the results in %BUILD_DIR%/doctest/output.txt.
	goto end
)

:end

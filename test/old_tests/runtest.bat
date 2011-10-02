@rem quick script to run Blender tests
@echo off

rem find Blender install path

set BLENDERHOME=
if [%1]==[] (
for /f "tokens=2* delims=	 " %%A in ('reg.exe query "HKLM\SOFTWARE\BlenderFoundation" /v Install_Dir') DO SET BLENDERHOME="%%B"
)

if not defined BLENDERHOME (
echo Blender not found! Cannot run tests.
goto end
)

echo.
echo Running tests...
echo.

%BLENDERHOME%\blender.exe -P runtest_skinning.py
%BLENDERHOME%\blender.exe -P runtest_havok.py
%BLENDERHOME%\blender.exe -P runtest_animation.py

echo.
echo Done!
echo.

:end

rem undefine variables

set BLENDERHOME=

pause

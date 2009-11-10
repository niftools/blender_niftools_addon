@rem quick and dirty linux shell script to install the scripts in a user's local blender dir
@echo off

rem find Blender install path

set BLENDERHOME=
set BLENDERSCRIPTS=
if [%1]==[] (
for /f "tokens=2* delims=	 " %%A in ('reg.exe query "HKLM\SOFTWARE\BlenderFoundation" /v Install_Dir') DO SET BLENDERHOME="%%B"
if defined BLENDERHOME echo Blender installation found from registry.
) else (
set BLENDERHOME=%1
echo Blender installation specified as argument.
)

if not defined BLENDERHOME (
echo Blender not found! Use
echo.
echo   install.bat "C:\Path\To\Blender"
echo.
echo to specify where to install the scripts.
goto endofinstall
)

echo Installing in:
echo.
echo   %BLENDERHOME%
echo.

if not exist %BLENDERHOME%\blender.exe (
echo blender.exe not found!
echo.
echo Invalid installation path? Use
echo.
echo   install.bat "C:\Path\To\Blender"
echo.
echo to specify where to install the scripts.
goto endofinstall
)

set BLENDERSCRIPTS=%BLENDERHOME%\.blender\scripts

rem remove clutter

echo Removing clutter

for %%A in (%BLENDERSCRIPTS%\nif_common.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\nif_common.pyc) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\export_nif.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\import_nif.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\mesh_niftools_weightsquash.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\mesh_niftools_hull.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\mesh_niftools_morphcopy.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\object_niftools_set_bone_priority.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\object_niftools_save_bone_pose.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\object_niftools_load_bone_pose.py) do if exist %%A del %%A
for %%A in (%BLENDERSCRIPTS%\bpymodules\nifImEx) do if exist %%A del /s %%A

rem make sure menu's get updated

echo Refreshing Blender menu's

for %%A in (%BLENDERHOME%\.blender\Bpymenus) do if exist %%A del %%A

rem install

echo Installing files

@echo on

@for %%A in (scripts\mesh\mesh_niftools_weightsquash.py, scripts\mesh\mesh_niftools_hull.py, scripts\mesh\mesh_niftools_morphcopy.py) do copy "%%A" %BLENDERSCRIPTS%\mesh

@for %%A in (scripts\object\object_niftools_set_bone_priority.py, scripts\object\object_niftools_save_bone_pose.py, scripts\object\object_niftools_load_bone_pose.py) do copy "%%A" %BLENDERSCRIPTS%\Object

@for %%A in (scripts\import\import_nif.py, ) do copy "%%A" %BLENDERSCRIPTS%\import

@for %%A in (scripts\export\export_nif.py, ) do copy "%%A" %BLENDERSCRIPTS%\export

@for %%A in (scripts\bpymodules\nif_common.py, scripts\bpymodules\nif_test.py) do copy "%%A" %BLENDERSCRIPTS%\bpymodules

@echo off

echo.
echo Done!
echo.

:endofinstall

rem undefine variables

set BLENDERHOME=
set BLENDERSCRIPTS=

pause

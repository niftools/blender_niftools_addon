@rem quick and dirty linux shell script to install the scripts in a user's local blender dir
@echo off

rem blender25 directory

set BLENDERHOME=..\blender25

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

echo on

@echo Removing clutter

@for %%A in (%BLENDERSCRIPTS%\io\import_nif.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\io\export_nif.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\import\import_nif.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\export\export_nif.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\nif_common.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\bpymodules\nif_common.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\mesh_weightsquash.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\mesh_hull.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\object_setbonepriority.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\object_savebonepose.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\object_loadbonepose.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\mesh\mesh_weightsquash.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\mesh\mesh_hull.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\mesh\mesh_morphcopy.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\object\object_setbonepriority.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\object\object_savebonepose.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\object\object_loadbonepose.py*) do if exist %%A del %%A
@for %%A in (%BLENDERSCRIPTS%\bpymodules\nifImEx) do if exist %%A del \s %%A

rem make sure menu's get updated

@echo Refreshing Blender menu's

@for %%A in (%BLENDERHOME%\.blender\Bpymenus) do if exist %%A del %%A

rem install

@echo Installing files

@for %%A in (io, op, modules) do mkdir %BLENDERSCRIPTS%\%%A

rem @for %%A in (scripts\mesh\mesh_niftools_weightsquash.py, scripts\mesh\mesh_niftools_hull.py, scripts\mesh\mesh_niftools_morphcopy.py) do copy "%%A" %BLENDERSCRIPTS%\mesh

rem @for %%A in (scripts\object\object_niftools_set_bone_priority.py, scripts\object\object_niftools_save_bone_pose.py, scripts\object\object_niftools_load_bone_pose.py) do copy "%%A" %BLENDERSCRIPTS%\object

@for %%A in (scripts\import\import_nif.py, ) do copy "%%A" %BLENDERSCRIPTS%\io

rem @for %%A in (scripts\export\export_nif.py, ) do copy "%%A" %BLENDERSCRIPTS%\io

@for %%A in (scripts\bpymodules\nif_common.py, scripts\bpymodules\nif_test.py) do copy "%%A" %BLENDERSCRIPTS%\modules

@echo off

echo.
echo Done!
echo.

:endofinstall

rem undefine variables

set BLENDERHOME=
set BLENDERSCRIPTS=

pause

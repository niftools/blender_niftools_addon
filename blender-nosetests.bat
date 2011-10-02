@echo off

if "%BLENDERHOME%" == "" (
  echo.Please set BLENDERHOME to the blender.exe folder
  goto end
)

%BLENDERHOME%\blender.exe --background --factory-startup --python blender-nosetests.py -- %*

:end

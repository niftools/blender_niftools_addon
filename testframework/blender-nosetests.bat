@echo off

if "%BLENDER_HOME%" == "" (
  echo. "Please set BLENDER_HOME to the blender.exe folder"
  goto end
)

"%BLENDER_HOME%\blender.exe" --background --factory-startup --python blender-nosetests.py -- %*

:end

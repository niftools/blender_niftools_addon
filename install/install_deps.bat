@echo off

:: Script to install developer dependancies for the Blender Nif Plugin

python -m pip install Sphinx --target="%APPDATABLENDERADDONS%modules"
python -m pip install nose --target="%APPDATABLENDERADDONS%\modules"
@echo off

:: Script to install developer dependancies for the Blender Nif Plugin

python -m pip install Sphinx --target="%BLENDER_ADDONS%\dependencies"
python -m pip install nose --target="%BLENDER_ADDONS%\dependencies"
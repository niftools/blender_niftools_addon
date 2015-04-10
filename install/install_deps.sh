#!/bin/sh

#Script to install developer dependancies for the Blender Nif Plugin

python3 -m pip install Sphinx --target="%APPDATABLENDERADDONS%/modules"
python3 -m pip install nose --target="%APPDATABLENDERADDONS%/modules"
#!/bin/sh

#Script to install developer dependancies for the Blender Nif Plugin
python -m pip install Sphinx --target="${BLENDER_ADDONS_DIR}\dependencies"
python -m pip install nose --target="${BLENDER_ADDONS_DIR}\dependencies"

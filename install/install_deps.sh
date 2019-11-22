#!/bin/sh

SCRIPT_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"

#Script to install developer dependencies for the Blender Nif Plugin
python -m pip install Sphinx --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}/dependencies"
python -m pip install nose --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}/dependencies"

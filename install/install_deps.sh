#!/bin/sh

SCRIPT_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"

#Script to install developer dependencies for the Blender Nif Plugin
python -m pip install Sphinx --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install nose --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install "PyFFI==2.2.4.dev2" --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"

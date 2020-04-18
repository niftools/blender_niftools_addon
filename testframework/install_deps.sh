#!/bin/bash
# Install developer dependencies for integration tests

echo "Installing dependencies to ${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install Sphinx --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install nose --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install "PyFFI==2.2.4.dev3" --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install "pydevd-pycharm~=201.6668.60" --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"

#!/bin/bash
# Install developer dependencies for integration tests
PYFFI_VERSION="2.2.4.dev4"
PYDEV_VERSION="201.6668.60"

echo "Installing dependencies to ${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install Sphinx --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install nose --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install "PyFFI==${PYFFI_VERSION}" --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"
python -m pip install "pydevd-pycharm~=${PYDEV_VERSION}" --target="${BLENDER_ADDONS_DIR:-${SCRIPT_DIR}}"

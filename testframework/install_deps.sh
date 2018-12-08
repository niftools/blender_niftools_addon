#!/bin/sh
# Install developer dependencies for integration tests

if [[ "${BLENDER_ADDONS_DIR}" == "" || ! -e "${BLENDER_ADDONS_DIR}"  ]]; then
    echo "Update BLENDER_ADDONS_DIR to the folder where the blender addons reside, such as:"
    echo "set BLENDER_ADDONS_DIR=~/Blender Foundation/Blender/2.79/scripts/addons"
    echo "\n"
    exit 1
fi

echo "Installing Sphinx to ${BLENDER_ADDONS_DIR}"
python -m pip install Sphinx nose pyffi --target="${BLENDER_ADDONS_DIR}"

# Currently installing pyffi from pypi fails for runtime classes
# python -m pip install pyffi --target="${BLENDER_ADDONS_DIR}"

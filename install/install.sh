#!/bin/sh

BUILD_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
TEMP="${BUILD_DIR}"/temp
ROOT="${BUILD_DIR}"/..
VERSION=`cat ${ROOT}/io_scene_nif/VERSION`
NAME="blender_nif_plugin"

function find_blender() {
    for BLENDER_VERSION in 2.79 2.78 2.77 2.76 2.75
    do
        BLENDER_ADDONS_DIR=~/.blender/"${BLENDER_VERSION}"/scripts/addons
        if [ -e ~/.blender/${BLENDER_VERSION}/ ]; then
            echo "Blender addons directory : ${BLENDER_ADDONS_DIR}"
            break
        fi
    done
    if [ ! -e ~/.blender/"${BLENDER_VERSION}"/ ]; then
        echo Blender addons folder not found.
        echo Start Blender at least once, save user preferences, and try again.
        exit 1
    fi
}

if [ ! -e "${BLENDER_ADDONS_DIR}" ]; then
    find_blender
else
    echo "Using ${BLENDER_ADDONS_DIR} as installation directory"
fi

echo "Installing to:"
echo "${BLENDER_ADDONS_DIR}"/io_scene_nif
# remove old files
rm -rf "${BLENDER_ADDONS_DIR}"/io_scene_nif/

# create zip
sh "${BUILD_DIR}"/makezip.sh

# copy files from repository to Blender addons folder
unzip -q "${TEMP}/${NAME}-${VERSION}.zip" -d "${BLENDER_ADDONS_DIR}"
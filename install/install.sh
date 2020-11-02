#!/bin/bash

BUILD_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"
TEMP="${BUILD_DIR}"/temp
ROOT="${BUILD_DIR}"/..
VERSION=$(cat "${ROOT}/io_scene_nif/VERSION.txt")
NAME="blender_niftools_addon"
HASH=$(git rev-parse --short HEAD)
DATE=$(date +%F)
ZIP_NAME="${NAME}-${VERSION}-${DATE}-${HASH}.zip"

echo "Blender addons directory : ${BLENDER_ADDONS_DIR}"
if [[ ! -e "${BLENDER_ADDONS_DIR}" ]]; then
    echo Blender addons folder not found.
    echo Start blender at least once, save user preferences, and try again.
    exit 1
else
    echo "Using ${BLENDER_ADDONS_DIR} as installation directory"
fi

PLUGIN_DIR="${BLENDER_ADDONS_DIR}"/io_scene_nif/
if [[ -d "${PLUGIN_DIR}" ]]; then
  echo "Installing to: ${PLUGIN_DIR}"
  echo "Removing old io_scene_nif directory ${PLUGIN_DIR}"
  rm -rf "${PLUGIN_DIR}"
else
  echo "Plugin directory does not exist"
  echo "Directory: ${PLUGIN_DIR}"
fi

# create zip
echo "Creating plugin zip file"
sh "${BUILD_DIR}"/makezip.sh || exit 1

# copy files from repository to blender addons folder
echo "Unzipping to ${PLUGIN_DIR}"
unzip -q "${TEMP}/${ZIP_NAME}" -d "${BLENDER_ADDONS_DIR}"

#!/bin/bash
CUR_DIR=$(pwd)
BUILD_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"
ROOT="${BUILD_DIR}"/..
PLUGIN_IN="${ROOT}"/io_scene_nif/
VERSION=$(cat "${PLUGIN_IN}"/VERSION)
NAME="blender_nif_plugin"
ZIP_NAME="${NAME}-${VERSION}.zip"
TEMP="${BUILD_DIR}"/temp
PLUGIN_OUT="${TEMP}"/io_scene_nif
DEPS_OUT="${PLUGIN_OUT}"/dependencies
PYFFI_VERSION="2.2.4.dev0"

if [[ -d "${TEMP}" ]]; then
  echo "Removing old temp directory"
  rm -rf "${TEMP}"
fi

mkdir "${TEMP}"

echo "Copying io_scene_nif directory"
cp -r "${PLUGIN_IN}" "${PLUGIN_OUT}"

echo "Creating dependencies folder"
python -m pip install "PyFFI==${PYFFI_VERSION}" --target="${DEPS_OUT:-${BUILD_DIR}/dependencies}"

echo "Copying loose files"
cp "${ROOT}"/AUTHORS.rst "${PLUGIN_OUT}"
cp "${ROOT}"/CHANGELOG.rst "${PLUGIN_OUT}"
cp "${ROOT}"/LICENSE.rst "${PLUGIN_OUT}"
cp "${ROOT}"/README.rst "${PLUGIN_OUT}"


echo "Creating zip ${ZIP_NAME}"
cd "${TEMP}" || exit
zip -9rq "${TEMP}/${ZIP_NAME}" ./io_scene_nif -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*/fileformat.dtd
cd "${CUR_DIR}" || exit

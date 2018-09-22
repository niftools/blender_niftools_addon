#!/bin/bash
CUR_DIR=$(pwd)
BUILD_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
ROOT="${BUILD_DIR}"/..
PLUGIN_IN="${ROOT}"/io_scene_nif/
VERSION=`cat "${PLUGIN_IN}"/VERSION`
NAME="blender_nif_plugin"
ZIP_NAME="${NAME}-${VERSION}.zip"
TEMP="${BUILD_DIR}"/temp
PLUGIN_OUT="${TEMP}"/io_scene_nif
DEPS_OUT="${PLUGIN_OUT}"/dependencies

#cd "${ROOT}"
#git clean -xfdq
#git submodule foreach --recursive git clean -xfdq
#cd "${DIR}"

if [ -d "${TEMP}" ]; then
  echo "Removing old temp directory"
  rm -rf "${TEMP}"
fi

mkdir "${TEMP}"

echo "Copying io_scene_nif directory"
cp -r "${PLUGIN_IN}" "${TEMP}"/

echo "Creating dependencies folder"
mkdir -p "${DEPS_OUT}"

echo "Moving pyffi to dependencies folder"
cp -r "${ROOT}"/pyffi/pyffi "${DEPS_OUT}"
cp "${ROOT}"/pyffi/*.rst "${DEPS_OUT}"/pyffi
rm -rf "${DEPS_OUT}"/pyffi/formats/cgf
rm -rf "${DEPS_OUT}"/pyffi/formats/dae
rm -rf "${DEPS_OUT}"/pyffi/formats/psk
rm -rf "${DEPS_OUT}"/pyffi/formats/rockstar
rm -rf "${DEPS_OUT}"/pyffi/formats/tga
rm -rf "${DEPS_OUT}"/pyffi/qskope

echo "Copying loose files"
cp "${ROOT}"/AUTHORS.rst "${PLUGIN_OUT}"
cp "${ROOT}"/CHANGELOG.rst "${PLUGIN_OUT}"
cp "${ROOT}"/LICENSE.rst "${PLUGIN_OUT}"
cp "${ROOT}"/README.rst "${PLUGIN_OUT}"


echo "Creating zip ${ZIP_NAME}"
cd "${TEMP}"
zip -9rq "${TEMP}/${ZIP_NAME}" ./io_scene_nif -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*/fileformat.dtd
cd "${CUR_DIR}"
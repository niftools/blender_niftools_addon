#!/bin/bash

PYFFI_VERSION="2.2.4.dev3"
NAME="blender_niftools_addon"
CUR_DIR=$(pwd)
BUILD_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"
ROOT="${BUILD_DIR}"/..
ADDON_IN="${ROOT}"/io_scene_niftools/
HASH=$(git rev-parse --short HEAD)
VERSION=$(cat "${ADDON_IN}/VERSION.txt")
DATE=$(date +%F)
ZIP_NAME="${NAME}-${VERSION}-${DATE}-${HASH}.zip"
TEMP="${BUILD_DIR}"/temp
ADDON_OUT="${TEMP}"/io_scene_niftools
DEPS_OUT="${ADDON_OUT}"/dependencies

echo "Creating Blender Niftools Addon addon zip"

echo "Checking for temp folder: ${TEMP}"
if [[ -d "${TEMP}" ]]; then
  echo "Removing old temp directory"
  rm -rf "${TEMP}"
else
  echo "No existing temp folder"
fi

mkdir "${TEMP}"

echo "Copying io_scene_niftools directory"
cp -r "${ADDON_IN}" "${ADDON_OUT}"

echo "Creating dependencies folder ${DEPS_OUT:-${BUILD_DIR}/dependencies}"
#python -m pip install -i https://test.pypi.org/simple/ PyFFI==2.2.4.dev5 --target="${DEPS_OUT:-${BUILD_DIR}/dependencies}"
python -m pip install "PyFFI==${PYFFI_VERSION}" --target="${DEPS_OUT:-${BUILD_DIR}/dependencies}"
docker compose up || exit 1

echo "Copying loose files"
cp "${ROOT}"/AUTHORS.rst "${ADDON_OUT}"
cp "${ROOT}"/CHANGELOG.rst "${ADDON_OUT}"
cp "${ROOT}"/LICENSE.rst "${ADDON_OUT}"
cp "${ROOT}"/README.rst "${ADDON_OUT}"

echo "Creating zip ${ZIP_NAME}"
cd "${TEMP}" || exit 1
zip -9rq "${TEMP}/${ZIP_NAME}" ./io_scene_niftools -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*/fileformat.dtd
cd "${CUR_DIR}" || exit 1

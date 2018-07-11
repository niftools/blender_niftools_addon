#!/bin/bash
DIR="$( cd "$(dirname "$0")" ; pwd -P )"
VERSION=`cat ${DIR}/../io_scene_nif/VERSION`
NAME="blender_nif_plugin"
ROOT=${DIR}/..
DEPS="io_scene_nif/dependencies"

cd ${ROOT}
git clean -xfdq
git submodule foreach --recursive git clean -xfdq
cd ${DIR}

rm -r ${DIR}/temp
mkdir ${DIR}/temp
cd ${DIR}/temp

echo "Copying io_scene_nif directory"
cp -r ${ROOT}/io_scene_nif .

echo "Creating dependencies folder"
mkdir ${DEPS}

echo "Moving pyffi to dependencies folder"
cp -r ${ROOT}/pyffi/pyffi ${DEPS}
cp ${ROOT}/pyffi/*.rst ${DEPS}/pyffi
rm -rf ${DEPS}/pyffi/formats/cgf
rm -rf ${DEPS}/pyffi/formats/dae
rm -rf ${DEPS}/pyffi/formats/psk
rm -rf ${DEPS}/pyffi/formats/rockstar
rm -rf ${DEPS}/pyffi/formats/tga
rm -rf ${DEPS}/pyffi/qskope

echo "Copying loose files"
cp ${ROOT}/AUTHORS.rst io_scene_nif
cp ${ROOT}/CHANGELOG.rst io_scene_nif
cp ${ROOT}/LICENSE.rst io_scene_nif
cp ${ROOT}/README.rst io_scene_nif

zip -9rq "${DIR}/${NAME}-${VERSION}.zip" io_scene_nif -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*/fileformat.dtd

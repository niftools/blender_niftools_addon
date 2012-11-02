#!/bin/sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VERSION=`cat ${DIR}/../io_scene_nif/VERSION`
NAME="blender_nif_plugin"
ROOT=${DIR}/..

pushd $ROOT
git clean -xfd
git submodule foreach --recursive git clean -xfd
popd

mkdir ${DIR}/temp

pushd ${DIR}/temp
cp -r ${ROOT}/io_scene_nif/ .
mkdir io_scene_nif/modules
cp -r ${ROOT}/pyffi/pyffi/ io_scene_nif/modules
cp ${ROOT}/pyffi/*.rst io_scene_nif/modules/pyffi
rm -r io_scene_nif/modules/pyffi/formats/cgf
rm -r io_scene_nif/modules/pyffi/formats/dae
rm -r io_scene_nif/modules/pyffi/formats/psk
rm -r io_scene_nif/modules/pyffi/formats/rockstar
rm -r io_scene_nif/modules/pyffi/formats/tga
rm -r io_scene_nif/modules/pyffi/qskope
cp ${ROOT}/AUTHORS.rst io_scene_nif
cp ${ROOT}/CHANGELOG.rst io_scene_nif
cp ${ROOT}/LICENSE.rst io_scene_nif
cp ${ROOT}/README.rst io_scene_nif
zip -9r "${DIR}/${NAME}-${VERSION}.zip" io_scene_nif -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*/fileformat.dtd
popd

rm -r ${DIR}/temp

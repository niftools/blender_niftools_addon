#!/bin/bash
DIR=`dirname $0`
VERSION=`cat ${DIR}/../io_scene_nif/VERSION`
NAME="blender_nif_plugin"
ROOT=${DIR}/..

cd $ROOT
git clean -xfdq
git submodule foreach --recursive git clean -xfdq
cd $DIR

mkdir ${DIR}/temp

cd ${DIR}/temp
cp -r ${ROOT}/io_scene_nif/ .
mkdir io_scene_nif/modules
cp -r ${ROOT}/pyffi/pyffi/ io_scene_nif/modules
cp ${ROOT}/pyffi/*.rst io_scene_nif/modules/pyffi
rm -rf io_scene_nif/modules/pyffi/formats/cgf
rm -rf io_scene_nif/modules/pyffi/formats/dae
rm -rf io_scene_nif/modules/pyffi/formats/psk
rm -rf io_scene_nif/modules/pyffi/formats/rockstar
rm -rf io_scene_nif/modules/pyffi/formats/tga
rm -rf io_scene_nif/modules/pyffi/qskope
cp ${ROOT}/AUTHORS.rst io_scene_nif
cp ${ROOT}/CHANGELOG.rst io_scene_nif
cp ${ROOT}/LICENSE.rst io_scene_nif
cp ${ROOT}/README.rst io_scene_nif
zip -9rq "${DIR}/${NAME}-${VERSION}.zip" io_scene_nif -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*/fileformat.dtd
cd $DIR

rm -r ${DIR}/temp

#!/bin/sh

VERSION=`cat ../io_scene_nif/VERSION`
NAME="blender_nif_plugin"

pushd ..
git clean -xfd
cp -r pyffi/pyffi io_scene_nif
rm -r io_scene_nif/pyffi/formats/cgf
rm -r io_scene_nif/pyffi/formats/dae
rm -r io_scene_nif/pyffi/formats/psk
rm -r io_scene_nif/pyffi/formats/rockstar
rm -r io_scene_nif/pyffi/formats/tga
rm -r io_scene_nif/pyffi/qskope
zip -9r "install/${NAME}-${VERSION}.zip" io_scene_nif -x \*/__pycache__/\* -x \*/.git\* -x \*/.project -x \*.dtd
rm -r io_scene_nif/pyffi
popd

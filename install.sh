#!/bin/sh

# quick and dirty linux shell script to install the scripts in a
# user's local blender dir

# blender25 directory

PYFFIHOME=../pyffi
BLENDERHOME=../blender25
BLENDERVERSION=2.57

# uninstall old files

rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/io_scene_nif/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/

# install scripts

mkdir -p $BLENDERHOME/$BLENDERVERSION/scripts/addons/io_scene_nif/

cp scripts/addons/io_scene_nif/__init__.py $BLENDERHOME/$BLENDERVERSION/scripts/addons/io_scene_nif/
cp scripts/addons/io_scene_nif/import_export_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/addons/io_scene_nif/
cp scripts/addons/io_scene_nif/export_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/addons/io_scene_nif/
cp scripts/addons/io_scene_nif/import_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/addons/io_scene_nif/

# install pyffi

pushd $PYFFIHOME
git checkout master
git clean -xfd
popd
mkdir -p $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/
cp -r $PYFFIHOME/pyffi/ $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/
# remove closed source parts of pyffi
rm $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/utils/mopper.exe
# remove unused parts of pyffi
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/fileformat.dtd
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/qskope/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/cgf/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/psk/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/esp/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/rockstar/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/tga/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/dae/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/object_models/xsd/
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/object_models/mex/
# remove .git folders from submodules
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/nif/nifxml/.git
rm -rf $BLENDERHOME/$BLENDERVERSION/scripts/addons/modules/pyffi/formats/kfm/kfmxml/.git

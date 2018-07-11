#!/bin/sh

DIR=`pwd`/`dirname $0`
VERSION=`cat ${DIR}/../io_scene_nif/VERSION`
NAME="blender_nif_plugin"

for BLENDER_VERSION in 2.79 2.78 2.77 2.76 2.75
do
  BLENDER_ADDONS=~/.blender/${BLENDER_VERSION}/scripts/addons
  if [ -e ~/.blender/${BLENDER_VERSION}/ ]
  then
    echo "Blender addons directory : ${BLENDER_ADDONS}"
    break
  fi
done
if [ ! -e ~/.blender/${BLENDER_VERSION}/ ]
then
  echo Blender addons folder not found.
  echo Start blender at least once, save user preferences, and try again.
  exit 1
fi

echo Installing to:
echo ${BLENDER_ADDONS}/io_scene_nif
mkdir -p ${BLENDER_ADDONS}

# remove old files
rm -rf ${BLENDER_ADDONS}/io_scene_nif/

# create zip
sh ${DIR}/makezip.sh

# copy files from repository to blender addons folder
unzip -q "${DIR}/${NAME}-${VERSION}.zip" -d ${BLENDER_ADDONS}

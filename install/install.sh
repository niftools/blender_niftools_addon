#!/bin/sh

DIR=`pwd`/`dirname $0`
VERSION=`cat ${DIR}/../io_scene_nif/VERSION`
NAME="blender_nif_plugin"

for BLENDERVERSION in 2.66 2.65 2.64 2.63 2.62
do
  BLENDERADDONS=~/.blender/$BLENDERVERSION/scripts/addons
  if [ -e ~/.blender/$BLENDERVERSION/ ]
  then
    break
  fi
done
if [ ! -e ~/.blender/$BLENDERVERSION/ ]
then
  echo Blender addons folder not found.
  echo Start blender at least once, save user preferences, and try again.
  exit 1
fi

echo Installing to:
echo $BLENDERADDONS/io_scene_nif
mkdir -p $BLENDERADDONS

# remove old files
rm -rf $BLENDERADDONS/io_scene_nif/

# create zip
sh ${DIR}/makezip.sh

# copy files from repository to blender addons folder
unzip -q "$DIR/$NAME-$VERSION.zip" -d $BLENDERADDONS

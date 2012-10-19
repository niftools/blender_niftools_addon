#!/bin/sh
# quick and dirty script to install the blender nif scripts

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

# remove old files
rm -rf $BLENDERADDONS/io_scene_nif/

# copy files from repository to blender addons folder
cp -r ../scripts/addons/io_scene_nif/ $BLENDERADDONS/

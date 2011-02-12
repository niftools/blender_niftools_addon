#!/bin/sh

# quick and dirty linux shell script to install the scripts in a
# user's local blender dir

# blender25 directory

BLENDERHOME=../blender25
BLENDERVERSION=2.56

# remove clutter

rm -f $BLENDERHOME/$BLENDERVERSION/scripts/io/import_nif.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/io/export_nif.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/import/import_nif.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/export/export_nif.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/nif_common.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/bpymodules/nif_common.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/mesh_weightsquash.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/mesh_hull.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/object_setbonepriority.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/object_savebonepose.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/object_loadbonepose.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/mesh/mesh_weightsquash.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/mesh/mesh_hull.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/mesh/mesh_morphcopy.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/object/object_setbonepriority.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/object/object_savebonepose.py*
rm -f $BLENDERHOME/$BLENDERVERSION/scripts/object/object_loadbonepose.py*

# install

mkdir -p $BLENDERHOME/$BLENDERVERSION/scripts/io/ $BLENDERHOME/$BLENDERVERSION/scripts/op/ $BLENDERHOME/$BLENDERVERSION/scripts/modules/

# not yet ready
#cp scripts/mesh/mesh_niftools_weightsquash.py scripts/mesh/mesh_niftools_hull.py scripts/mesh/mesh_niftools_morphcopy.py $BLENDERHOME/$BLENDERVERSION/scripts/op/

cp scripts/import/import_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/io/
# not sure if needed, commented out for now
#cp scripts/import/import_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/ # workaround for nif_test import

# not yet ready
#cp scripts/export/export_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/io/
# not sure if needed, commented out for now
#cp scripts/export/export_nif.py $BLENDERHOME/$BLENDERVERSION/scripts/ # workaround for nif_test import

# not yet ready
#cp scripts/object/object_niftools_set_bone_priority.py scripts/object/object_niftools_save_bone_pose.py scripts/object/object_niftools_load_bone_pose.py $BLENDERHOME/$BLENDERVERSION/scripts/op/

cp scripts/bpymodules/nif_common.py scripts/bpymodules/nif_test.py $BLENDERHOME/$BLENDERVERSION/scripts/modules/

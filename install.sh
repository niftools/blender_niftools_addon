#!/bin/sh

# quick and dirty linux shell script to install the scripts in a
# user's local blender dir

# blender25 directory

BLENDERHOME=../blender25

# remove clutter

rm -f $BLENDERHOME/2.52/scripts/io/import_nif.py*
rm -f $BLENDERHOME/2.52/scripts/io/export_nif.py*
rm -f $BLENDERHOME/2.52/scripts/import/import_nif.py*
rm -f $BLENDERHOME/2.52/scripts/export/export_nif.py*
rm -f $BLENDERHOME/2.52/scripts/nif_common.py*
rm -f $BLENDERHOME/2.52/scripts/bpymodules/nif_common.py*
rm -f $BLENDERHOME/2.52/scripts/mesh_weightsquash.py*
rm -f $BLENDERHOME/2.52/scripts/mesh_hull.py*
rm -f $BLENDERHOME/2.52/scripts/object_setbonepriority.py*
rm -f $BLENDERHOME/2.52/scripts/object_savebonepose.py*
rm -f $BLENDERHOME/2.52/scripts/object_loadbonepose.py*
rm -f $BLENDERHOME/2.52/scripts/mesh/mesh_weightsquash.py*
rm -f $BLENDERHOME/2.52/scripts/mesh/mesh_hull.py*
rm -f $BLENDERHOME/2.52/scripts/mesh/mesh_morphcopy.py*
rm -f $BLENDERHOME/2.52/scripts/object/object_setbonepriority.py*
rm -f $BLENDERHOME/2.52/scripts/object/object_savebonepose.py*
rm -f $BLENDERHOME/2.52/scripts/object/object_loadbonepose.py*

# install

mkdir -p $BLENDERHOME/2.52/scripts/io/ $BLENDERHOME/2.52/scripts/op/ $BLENDERHOME/2.52/scripts/modules/

# not yet ready
#cp scripts/mesh/mesh_niftools_weightsquash.py scripts/mesh/mesh_niftools_hull.py scripts/mesh/mesh_niftools_morphcopy.py $BLENDERHOME/2.52/scripts/op/

cp scripts/import/import_nif.py $BLENDERHOME/2.52/scripts/io/
# not sure if needed, commented out for now
#cp scripts/import/import_nif.py $BLENDERHOME/2.52/scripts/ # workaround for nif_test import

# not yet ready
#cp scripts/export/export_nif.py $BLENDERHOME/2.52/scripts/io/
# not sure if needed, commented out for now
#cp scripts/export/export_nif.py $BLENDERHOME/2.52/scripts/ # workaround for nif_test import

# not yet ready
#cp scripts/object/object_niftools_set_bone_priority.py scripts/object/object_niftools_save_bone_pose.py scripts/object/object_niftools_load_bone_pose.py $BLENDERHOME/2.52/scripts/op/

cp scripts/bpymodules/nif_common.py scripts/bpymodules/nif_test.py $BLENDERHOME/2.52/scripts/modules/

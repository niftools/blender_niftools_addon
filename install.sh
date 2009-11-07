#!/bin/sh

# quick and dirty linux shell script to install the scripts in a user's local blender dir

# remove clutter

rm -f ~/.blender/scripts/nif_import.py*
rm -f ~/.blender/scripts/nif_export.py*
rm -f ~/.blender/scripts/import_nif.py*
rm -f ~/.blender/scripts/export_nif.py*
rm -f ~/.blender/scripts/import/import_nif.py*
rm -f ~/.blender/scripts/export/export_nif.py*
rm -f ~/.blender/scripts/nif_common.py*
rm -f ~/.blender/scripts/bpymodules/nif_common.py*
rm -f ~/.blender/scripts/mesh_weightsquash.py*
rm -f ~/.blender/scripts/mesh_hull.py*
rm -f ~/.blender/scripts/object_setbonepriority.py*
rm -f ~/.blender/scripts/object_savebonepose.py*
rm -f ~/.blender/scripts/object_loadbonepose.py*
rm -f ~/.blender/scripts/mesh/mesh_weightsquash.py*
rm -f ~/.blender/scripts/mesh/mesh_hull.py*
rm -f ~/.blender/scripts/object/object_setbonepriority.py*
rm -f ~/.blender/scripts/object/object_savebonepose.py*
rm -f ~/.blender/scripts/object/object_loadbonepose.py*
rm -rf ~/.blender/scripts/bpymodules/nifImEx

# make sure menu's get updated

rm -f ~/.blender/Bpymenus

# install

mkdir -p ~/.blender/scripts/import/ ~/.blender/scripts/export/ ~/.blender/scripts/mesh/ ~/.blender/scripts/object/ ~/.blender/scripts/bpymodules/

cp scripts/mesh/mesh_niftools_weightsquash.py scripts/mesh/mesh_niftools_hull.py ~/.blender/scripts/mesh/

cp scripts/import/import_nif.py ~/.blender/scripts/import/
cp scripts/import/import_nif.py ~/.blender/scripts/ # workaround for nif_test import

cp scripts/export/export_nif.py ~/.blender/scripts/export/
cp scripts/export/export_nif.py ~/.blender/scripts/ # workaround for nif_test import

cp scripts/object/object_niftools_set_bone_priority.py scripts/object/object_niftools_save_bone_pose.py scripts/object/object_niftools_load_bone_pose.py ~/.blender/scripts/object/

cp scripts/bpymodules/nif_common.py scripts/bpymodules/nif_test.py ~/.blender/scripts/bpymodules/


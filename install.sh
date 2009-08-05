#!/bin/sh

# quick and dirty linux shell script to install the scripts in a user's local blender dir

# remove clutter

rm -f ~/.blender/scripts/nif_import.py*
rm -f ~/.blender/scripts/nif_export.py*
rm -f ~/.blender/scripts/import_nif.py*
rm -f ~/.blender/scripts/export_nif.py*
rm -f ~/.blender/scripts/nif_common.py*
rm -f ~/.blender/scripts/bpymodules/nif_common.py*
rm -f ~/.blender/scripts/mesh_weightsquash.py*
rm -f ~/.blender/scripts/mesh_hull.py*
rm -f ~/.blender/scripts/object_setbonepriority.py*
rm -f ~/.blender/scripts/object_savebonepose.py*
rm -f ~/.blender/scripts/object_loadbonepose.py*
rm -rf ~/.blender/scripts/bpymodules/nifImEx

# make sure menu's get updated

rm -f ~/.blender/Bpymenus

# install

cp scripts/import_nif.py scripts/export_nif.py scripts/mesh_niftools_weightsquash.py scripts/mesh_niftools_hull.py scripts/object_niftools_set_bone_priority.py scripts/object_niftools_save_bone_pose.py scripts/object_niftools_load_bone_pose.py ~/.blender/scripts

cp scripts/bpymodules/nif_common.py scripts/bpymodules/nif_test.py ~/.blender/scripts/bpymodules


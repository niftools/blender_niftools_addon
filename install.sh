#!/bin/sh

# quick and dirty linux shell script to install the scripts in a user's local blender dir

# remove clutter

rm -f ~/.blender/scripts/nif_common.py
rm -f ~/.blender/scripts/nif_common.pyc
rm -rf ~/.blender/scripts/bpymodules/nifImEx

# install

cp scripts/nif_import.py scripts/nif_export.py scripts/mesh_weightsquash.py scripts/mesh_hull.py ~/.blender/scripts

cp scripts/bpymodules/nif_common.py ~/.blender/scripts/bpymodules


#!/bin/sh

# quick and dirty linux shell script to install the scripts in a user's local blender dir

cp scripts/nif_import.py scripts/nif_export.py scripts/mesh_weightsquash.py ~/.blender/scripts
mkdir -p ~/.blender/scripts/bpymodules/nifImEx
cp scripts/bpymodules/nifImEx/__init__.py scripts/bpymodules/nifImEx/Config.py  scripts/bpymodules/nifImEx/Defaults.py scripts/bpymodules/nifImEx/Read.py scripts/bpymodules/nifImEx/Write.py scripts/bpymodules/nifImEx/niftools_logo.png ~/.blender/scripts/bpymodules/nifImEx

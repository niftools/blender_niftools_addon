#!/bin/bash
cp -r pyffi/pyffi io_scene_nif
blender --background --factory-startup --python blender-nosetests.py -- $@


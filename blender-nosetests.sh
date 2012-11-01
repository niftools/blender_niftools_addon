#!/bin/bash
blender --background --factory-startup --python blender-nosetests.py -- $@

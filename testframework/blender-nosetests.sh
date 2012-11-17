#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
blender --background --factory-startup --python $DIR/blender-nosetests.py -- $@

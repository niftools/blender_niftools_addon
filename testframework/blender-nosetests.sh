#!/bin/bash

if [[ "${BLENDER_HOME}" == "" ]]; then
  echo "Please set BLENDER_HOME to the blender.exe folder"
  exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
"${BLENDER_HOME}"/blender --background --factory-startup --python "${DIR}"/blender-nosetests.py -- $@

#!/bin/bash

python3 codegen.py
mv /codegen/cobra-tools/generated /output
# TODO: only move the formats we need to reduce bloat
echo "Done"
exit

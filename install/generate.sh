#!/bin/bash

python3 codegen.py
rm -r /output/*
mkdir -p /output/generated/formats
cd /codegen/cobra-tools/generated || exit 1
# Everything is ~4.3MB while just taking the formats we need is just ~2.8MB
mv ./formats/base /output/generated/formats
mv ./formats/dds /output/generated/formats
mv ./formats/nif /output/generated/formats
mv ./spells /output/generated
mv ./utils /output/generated
echo "Done"
exit

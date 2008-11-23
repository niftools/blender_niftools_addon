#!/usr/bin/python

"""Create bind pose nif for Fallout 3."""

from __future__ import with_statement
from contextlib import closing

from PyFFI.Formats.NIF import NifFormat

# read skeleton
skeleton = NifFormat.Data()
with closing(open("skeleton.nif", "rb")) as stream:
    skeleton.read(stream)
# merge all body parts
for bodypartnif in ("femaleupperbody.nif",
                    "femalerighthand.nif",
                    "femalelefthand.nif",
                    "headfemale.nif"):
    bodypart = NifFormat.Data()
    with closing(open(bodypartnif, "rb")) as stream:
        bodypart.read(stream)
        skeleton.roots[0].mergeExternalSkeletonRoot(bodypart.roots[0])
# send all bones to their bind position
for block in skeleton.roots[0].tree():
    if isinstance(block, NifFormat.NiGeometry):
        block.sendBonesToBindPosition()
# remove non-ninode children
for block in skeleton.roots[0].tree():
    block.setChildren([child
                       for child in block.getChildren()
                       if isinstance(child, NifFormat.NiNode)])
    block.setExtraDatas([])
    block.setProperties([])
    block.controller = None
    block.collisionObject = None

# write result
with closing(open("fo3_bodybindpose.nif", "wb")) as stream:
    skeleton.write(stream)

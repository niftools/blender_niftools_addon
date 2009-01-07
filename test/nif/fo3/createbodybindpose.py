#!/usr/bin/python

"""Create bind pose nif for Fallout 3."""

from __future__ import with_statement
from contextlib import closing
import logging

from PyFFI.Formats.NIF import NifFormat

# set up logger
niftoolslogger = logging.getLogger("niftools")
niftoolslogger.setLevel(logging.DEBUG)
pyffilogger = logging.getLogger("pyffi")
pyffilogger.setLevel(logging.INFO)
loghandler = logging.StreamHandler()
loghandler.setLevel(logging.DEBUG)
logformatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
loghandler.setFormatter(logformatter)
niftoolslogger.addHandler(loghandler)
pyffilogger.addHandler(loghandler)

logger = logging.getLogger("niftools.blender.test")

# read skeleton
logger.info("Reading skeleton.nif")
skeleton = NifFormat.Data()
with closing(open("skeleton.nif", "rb")) as stream:
    skeleton.read(stream)

# merge all body parts
for bodypartnif in ("femaleupperbody.nif",
                    "femalerighthand.nif",
                    "femalelefthand.nif",
                    "headfemale.nif"):
    logger.info("Merging body part %s" % bodypartnif)
    bodypart = NifFormat.Data()
    with closing(open(bodypartnif, "rb")) as stream:
        bodypart.read(stream)
        skeleton.roots[0].mergeExternalSkeletonRoot(bodypart.roots[0])
# send geometries to their bind position
logger.info("Sending geometries to bind position")
skeleton.roots[0].sendGeometriesToBindPosition()
# send all bones to their bind position
logger.info("Sending bones to bind position")
for block in skeleton.roots[0].tree():
    if isinstance(block, NifFormat.NiGeometry):
        block.sendBonesToBindPosition()
# remove non-ninode children
logger.info("Removing non-NiNode children")
for block in skeleton.roots[0].tree():
    block.setChildren([child
                       for child in block.getChildren()
                       if isinstance(child, NifFormat.NiNode)])
    block.setExtraDatas([])
    block.setProperties([])
    block.controller = None
    block.collisionObject = None

# write result
logger.info("Writing fo3_bodybindpose.nif")
with closing(open("fo3_bodybindpose.nif", "wb")) as stream:
    skeleton.write(stream)

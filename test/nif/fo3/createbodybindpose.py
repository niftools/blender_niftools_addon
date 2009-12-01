#!/usr/bin/python

"""Create bind pose nif for Fallout 3."""

from __future__ import with_statement
from contextlib import closing
import logging

from pyffi.formats.nif import NifFormat

# set up logger
niftoolslogger = logging.getLogger("niftools")
niftoolslogger.setLevel(logging.DEBUG)
pyffilogger = logging.getLogger("pyffi")
pyffilogger.setLevel(logging.DEBUG)
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
        skeleton.roots[0].merge_external_skeleton_root(bodypart.roots[0])
# send geometries to their bind position
logger.info("Sending geometries to bind position")
skeleton.roots[0].send_geometries_to_bind_position()
# send all bones to their bind position
logger.info("Sending bones to bind position")
skeleton.roots[0].send_bones_to_bind_position()
#for block in skeleton.roots[0].tree():
#    if isinstance(block, NifFormat.NiGeometry):
#        block.send_bones_to_bind_position()
# remove non-ninode children
#logger.info("Removing non-NiNode children")
#for block in skeleton.roots[0].tree():
#    block.set_children([child
#                       for child in block.get_children()
#                       if isinstance(child, NifFormat.NiNode)])
#    block.set_extra_datas([])
#    block.set_properties([])
#    block.controller = None
#    block.collision_object = None

# write result
logger.info("Writing fo3_bodybindpose.nif")
with closing(open("fo3_bodybindpose.nif", "wb")) as stream:
    skeleton.write(stream)

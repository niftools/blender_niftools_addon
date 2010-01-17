"""Create bind pose nif for Fallout 3, and check animation."""

from __future__ import with_statement
import logging
import os.path

from pyffi.formats.nif import NifFormat

from nif_test import TestSuite

class AnimationTestSuite(TestSuite):
    def run(self):
        self.make_fo3_fullbody()
        self.test(
            filename="test/nif/fo3/_fullbody.nif",
            config=dict(
                IMPORT_TEXTURE_PATH=[self.config.get("path", "fallout3")]))

    def make_fo3_fullbody(self):
        if os.path.exists("test/nif/fo3/_fullbody.nif"):
            # to save time, only create the full body nif if it does
            # not yet exist
            return
        # fo3 body path
        fo3_male = os.path.join(
            self.config.get("path", "fallout3"),
            "meshes", "characters", "_male")
        # read skeleton
        self.logger.info("Reading skeleton.nif")
        skeleton = NifFormat.Data()
        with open(os.path.join(fo3_male, "skeleton.nif"), "rb") as stream:
            skeleton.read(stream)

        # merge all body parts
        for bodypartnif in ("femaleupperbody.nif",
                            "femalerighthand.nif",
                            "femalelefthand.nif",
                            "../head/headfemale.nif"):
            self.logger.info("Merging body part %s" % bodypartnif)
            bodypart = NifFormat.Data()
            with open(os.path.join(fo3_male, bodypartnif), "rb") as stream:
                bodypart.read(stream)
                skeleton.roots[0].merge_external_skeleton_root(bodypart.roots[0])
        # send geometries to their bind position
        self.logger.info("Sending geometries to bind position")
        skeleton.roots[0].send_geometries_to_bind_position()
        # send all bones to their bind position
        self.logger.info("Sending bones to bind position")
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
        self.logger.info("Writing fo3_bodybindpose.nif")
        with open("test/nif/fo3/_fullbody.nif", "wb") as stream:
            skeleton.write(stream)

suite = AnimationTestSuite("fo3_animation")
suite.run()

"""Automated tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2011, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****

import ConfigParser
import logging
import os.path

import Blender
from import_nif import NifImport
from export_nif import NifExport
from nif_common import NifConfig
from nif_common import NifFormat

class TestSuite:
    """A test suite class.

    @ivar scene: The Blender scene for this test suite.
    @type scene: Blender.Scene.Scene
    @ivar layer: The current Blender layer in the scene.
    @type layer: C{int}
    """
    def __init__(self, name, ini_filename="test/nif/test.ini"):
        """Initialize a new test suite with given name.

        @param name: The name of the test (will be used as name of the scene
            for this test).
        @type name: C{str}
        """
        self.context.scene = Blender.Scene.New(name) # new scene
        self.layer = 1 # current layer

        # set active scene
        self.context.scene.makeCurrent()
        # set active layer
        self.context.scene.setLayers([self.layer])

        # get configuration
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(ini_filename))

    def test(self, filename=None, config=None, selection=None, next_layer=None):
        """Run given test, and increase layer after export.

        @param filename: The name of the file to test.
        @type filename: C{str}
        @param config: Configuration options that differ from their default
            values. If the dictionary has the key game then the
            selection is exported, otherwise a file is imported. Optional.
        @type config: C{dict}
        @param selection: List of names of objects to select before running
            the test. Optional.
        @type selection: C{list} of C{str}
        @param next_layer: Whether or not to advance a layer after the test.
            If C{None} (default) then a layer is advanced only after export.
        @type next_layer: C{bool} or C{NoneType}
        @return: The import or export object.
        @rtype: L{NifImport} or L{NifExport}
        """

        if filename is None:
            raise ValueError("A test must specify a filename.")
        if config is None:
            config = {}
        if selection is None:
            selection = []

        # select objects
        self.context.scene.objects.selected = [
            ob for ob in self.context.scene.objects if ob.name in selection]

        # set script configuration
        finalconfig = dict(**NifConfig.DEFAULTS)
        logging.getLogger("niftools").setLevel(logging.DEBUG)
        logging.getLogger("pyffi").setLevel(logging.WARNING)

        for key, value in list(config.items()):
            finalconfig[key] = value

        # run test
        if 'game' in config:
            # export the imported files
            self.info(f"Exporting {filename}")

            finalconfig["EXPORT_FILE"] = filename
            result = NifExport(**finalconfig)

            # increment active layer for next import
            # different tests are put into different blender layers,
            # so the results can be easily visually inspected
            if next_layer in (None, True):
                self.layer += 1
                self.context.scene.setLayers([self.layer])

            # return test result
            return result
        else:
            self.info(f"Importing {filename}")

            # import file and return test result
            finalconfig["IMPORT_FILE"] =  filename
            result = NifImport(**finalconfig)

            if next_layer is True:
                self.layer += 1
                self.context.scene.setLayers([self.layer])

            return result

    def make_fo3_fullbody(self):
        if (os.path.exists("test/nif/fo3/_fullbody.nif")
            and os.path.exists("test/nif/fo3/skeleton.nif")):
            # to save time, only create the full body nif if it does
            # not yet exist
            return
        # fo3 body path
        fo3_male = os.path.join(
            self.config.get("path", "fallout3"),
            "meshes", "characters", "_male")
        # read skeleton
        self.info("Reading skeleton.nif")
        skeleton = NifFormat.Data()
        with open(os.path.join(fo3_male, "skeleton.nif"), "rb") as stream:
            skeleton.read(stream)

        # merge all body parts
        for bodypartnif in ("femaleupperbody.nif",
                            "femalerighthand.nif",
                            "femalelefthand.nif",
                            "../head/headfemale.nif"):
            self.info(f"Merging body part {bodypartnif}")
            bodypart = NifFormat.Data()
            with open(os.path.join(fo3_male, bodypartnif), "rb") as stream:
                bodypart.read(stream)
                skeleton.roots[0].merge_external_skeleton_root(bodypart.roots[0])
        # send geometries to their bind position
        self.info("Sending geometries to bind position")
        skeleton.roots[0].send_geometries_to_bind_position()
        # send all bones to their bind position
        self.info("Sending bones to bind position")
        skeleton.roots[0].send_bones_to_bind_position()
        # write result
        self.info("Writing fullbody.nif")
        with open("test/nif/fo3/_fullbody.nif", "wb") as stream:
            skeleton.write(stream)
        # create fixed skeleton.nif
        for block in skeleton.roots[0].tree():
            if isinstance(block, NifFormat.NiGeometry):
                block.send_bones_to_bind_position()
        # remove non-ninode children
        self.info("Removing non-NiNode children")
        for block in skeleton.roots[0].tree():
            block.set_children([child
                               for child in block.get_children()
                               if isinstance(child, NifFormat.NiNode)])
            block.set_extra_datas([])
            block.set_properties([])
            block.controller = None
            block.collision_object = None
        self.info("Writing skeleton.nif")
        with open("test/nif/fo3/skeleton.nif", "wb") as stream:
            skeleton.write(stream)

    def assert_equal(self, val1, val2):
        if isinstance(val1, int):
            assert(isinstance(val2, int))
            assert(val1 == val2)
        elif isinstance(val1, float):
            assert(isinstance(val2, float))
            assert(abs(val1 - val2) < 0.000001)
        else:
            raise TypeError(f"don't know how to test equality of "
                            f"{val1.__class__} and {val2.__class__}")

    def run(self):
        """Run the test suite. Override."""
        raise NotImplementedError

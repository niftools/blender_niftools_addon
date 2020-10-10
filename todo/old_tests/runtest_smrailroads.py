"""Automated Sid Meier's Railroads tests for the blender nif scripts."""

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
# ***** END LICENSE BLOCK *****

import logging
from itertools import izip

import Blender
from nif_test import TestSuite
from pyffi.formats.nif import NifFormat

# some tests to import and export nif files

class SMRailroadsTestSuite(TestSuite):
    def hasNoSpecProp(self, block):
        self.info("Has no specular property?")
        return all((not isinstance(prop, NifFormat.NiSpecularProperty))
                   for prop in block.properties)

    def hasVColProp(self, block):
        self.info("Has vertex color property?")
        return any(isinstance(prop, NifFormat.NiVertexColorProperty)
                   for prop in block.properties)

    def hasZBufProp(self, block):
        self.info("Has z-buffer property?")
        return any(isinstance(prop, NifFormat.NiZBufferProperty)
                   for prop in block.properties)

    def hasIntegerExtra(self, trishape, name, value):
        self.info(f"Has {name} with value {value:d}?")
        for extra in trishape.get_extra_datas():
            if (isinstance(extra, NifFormat.NiIntegerExtraData)
                and extra.name == name):
                # success if value matches
                return (extra.integer_data == value)
        # extra block not found: failure
        return False

    def has_shader_texture(self, texprop, name, shaderindex):
        self.info(f"Has shader texture {name} at index {shaderindex}?")
        shader_tex_desc = texprop.shader_textures[shaderindex]
        return shader_tex_desc.texture_data.source.file_name.lower() == name.lower()

    def checkSMRailRoads(self, root_block):
        # sanity check
        assert(isinstance(root_block, NifFormat.NiNode))

        # find geom
        geom = root_block.find(block_type=NifFormat.NiGeometry)

        # root block property test
        assert(self.hasVColProp(root_block))

        assert(self.hasZBufProp(root_block))

        # geometry property test
        assert(self.hasNoSpecProp(geom))

        # geometry extra data test
        assert(self.hasIntegerExtra(geom, "EnvironmentIntensityIndex", 3))
        assert(self.hasIntegerExtra(geom, "EnvironmentMapIndex", 0))
        assert(self.hasIntegerExtra(geom, "LightCubeMapIndex", 4))
        assert(self.hasIntegerExtra(geom, "NormalMapIndex", 1))
        assert(self.hasIntegerExtra(geom, "ShadowTextureIndex", 5))
        assert(self.hasIntegerExtra(geom, "SpecularIntensityIndex", 2))

        # find texturing property
        texprop = geom.find(block_type=NifFormat.NiTexturingProperty)

        # geometry diffuse texture test
        self.info("Checking base texture.")
        assert(texprop.has_base_texture)
        assert(texprop.base_texture.source.file_name[-9:].lower() == "_diff.dds")
        texbasename = texprop.base_texture.source.file_name[:-9]

        # geometry shader textures
        assert(self.has_shader_texture(texprop, "RRT_Engine_Env_map.dds", 0))
        assert(self.has_shader_texture(texprop, texbasename + "_NRML.dds", 1))
        assert(self.has_shader_texture(texprop, texbasename + "_SPEC.dds", 2))
        assert(self.has_shader_texture(texprop, texbasename + "_EMSK.dds", 3))
        assert(self.has_shader_texture(texprop, "RRT_Cube_Light_map_128.dds", 4))
        # note: 5 is apparently never used, although it has an extra index

        # check ninode flag
        assert(root_block.flags == 16)
        assert(geom.flags == 16)

    def run(self):
        nif_import = self.test(
            filename = 'test/nif/smrailroads1.nif')
        root_block = nif_import.root_blocks[0]
        # this is a generic regression test of the test itself
        # the original nif MUST pass it (if not there is a bug in the
        # testing code)
        self.info(
            "Checking original nif (for regression, MUST succeed).")
        self.checkSMRailRoads(root_block)

        # check that specularity was imported (these nifs do not have specular
        # properties)
        self.info("Checking specular color import.")
        testgeom = root_block.find(block_type=NifFormat.NiGeometry,
                                   block_name="Test")
        nifspec = testgeom.find(block_type=NifFormat.NiMaterialProperty).specular_color
        blendermat = Blender.Object.Get("Test").data.materials[0]
        assert(abs(blendermat.getSpec() - 1.0) < 1e-5)
        blenderspec = blendermat.getSpecCol()
        assert(abs(nifspec.r - blenderspec[0]) < 1e-5)
        assert(abs(nifspec.g - blenderspec[1]) < 1e-5)
        assert(abs(nifspec.b - blenderspec[2]) < 1e-5)

        nif_export = self.test(
            filename = 'test/nif/_smrailroads1.nif',
            config = dict(game = 'SID_MEIER_S_RAILROADS'),
            selection = ['Test'])
        root_block = nif_export.root_blocks[0]

        # check exported specularity
        self.info("Checking specular color export.")
        testgeom_export = root_block.find(block_type=NifFormat.NiGeometry,
                                   block_name="Test")
        nifspec_export = testgeom.find(block_type=NifFormat.NiMaterialProperty).specular_color
        assert(abs(nifspec.r - nifspec_export.r) < 1e-5)
        assert(abs(nifspec.g - nifspec_export.g) < 1e-5)
        assert(abs(nifspec.b - nifspec_export.b) < 1e-5)

        self.info("Checking alpha flags and threshold export.")
        nifalpha_export = testgeom_export.find(block_type=NifFormat.NiAlphaProperty)
        assert(nifalpha_export.flags == 13037)
        assert(nifalpha_export.threshold == 150)

        self.info("Checking extra shader export.")
        assert(testgeom_export.has_shader)
        assert(testgeom_export.shader_name == "RRT_NormalMap_Spec_Env_CubeLight")

        # check that the re-exported file still passes the check
        self.info("Checking exported nif...")
        self.checkSMRailRoads(root_block)

suite = SMRailroadsTestSuite("smrailroads")
suite.run()


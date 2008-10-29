"""Automated skinning tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007-2008, NIF File Format Library and Tools
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

from itertools import izip

import Blender
from nif_test import TestSuite
from PyFFI.Formats.NIF import NifFormat

# some tests to import and export nif files

class StencilTestSuite(TestSuite):
    def isTwoSided(self, b_mesh):
        return b_mesh.data.mode & Blender.Mesh.Modes.TWOSIDED

    def hasStencil(self, nif_geom):
        return any(isinstance(prop, NifFormat.NiStencilProperty)
                   for prop in nif_geom.properties)

    def run(self):
        # stencil test
        self.test(
            filename = 'test/nif/stenciltest.nif')
        assert(self.isTwoSided(Blender.Object.Get("Stencil")))
        assert(not self.isTwoSided(Blender.Object.Get("NoStencil")))
        nif_export = self.test(
            filename = 'test/nif/_stenciltest.nif',
            config = dict(EXPORT_VERSION = 'Oblivion'),
            selection = ['NoStencil', 'Stencil'])
        nif_stencil = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiGeometry, block_name = "Stencil")
        nif_nostencil = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiGeometry, block_name = "NoStencil")
        assert(self.hasStencil(nif_stencil))
        assert(not self.hasStencil(nif_nostencil))

        # alpha property test
        self.test(
            filename = 'test/nif/alphatest.nif')
        alpha_obj = Blender.Object.Get("Alpha")
        # check Z transparency
        assert(alpha_obj.data.materials[0].mode & Blender.Material.Modes.ZTRANSP)
        # check that transparency was exported
        alpha_obj_alpha = alpha_obj.data.materials[0].alpha
        assert(alpha_obj_alpha < 0.99)
        nif_export = self.test(
            filename = 'test/nif/_alphatest.nif',
            config = dict(EXPORT_VERSION = 'Oblivion'),
            selection = ['Alpha'])
        nif_alpha = nif_export.root_blocks[0].find(
            block_type = NifFormat.NiGeometry, block_name = "Alpha")
        nif_alpha_mat = nif_alpha.find(
            block_type = NifFormat.NiMaterialProperty)
        nif_alpha_alpha = nif_alpha.find(
            block_type = NifFormat.NiAlphaProperty)
        assert(nif_alpha_alpha.flags == 0x12ED)
        assert(nif_alpha_mat.alpha == alpha_obj_alpha)

suite = StencilTestSuite("stencil_alpha")
suite.run()


"""Automated NiLODNode test for the blender nif scripts."""

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

import Blender
from nif_test import TestSuite
from pyffi.formats.nif import NifFormat

# some tests to import and export nif files

class LODTestSuite(TestSuite):

    def run(self):
        self.test_lod()

    def test_lod(self):
        """LOD test."""
        def check_lodnode(root):
            lodnode = root.children[0]
            assert(isinstance(lodnode, NifFormat.NiLODNode))
            assert(lodnode.num_children == 2)
            assert(isinstance(lodnode.children[0], NifFormat.NiTriBasedGeom))
            assert(isinstance(lodnode.children[1], NifFormat.NiTriBasedGeom))
            assert(lodnode.children[0].data.num_vertices == 26)
            assert(lodnode.children[1].data.num_vertices == 8)
            range_data = lodnode.lod_level_data
            assert(range_data.num_lod_levels == lodnode.num_children)
            assert(range_data.lod_levels[0].near_extent == 0)
            assert(range_data.lod_levels[0].far_extent == 400)
            assert(range_data.lod_levels[1].near_extent == 400)
            assert(range_data.lod_levels[1].far_extent == 100000)
        # import
        nif_import = self.test(
            filename='test/nif/ee2/lodtest.nif',
            config=dict(
                IMPORT_SCALE_CORRECTION=1))
        # check that we have two lod children
        b_lod = Blender.Object.Get("Cube")
        assert(Blender.Object.Get("Cube_LOD0").parent == b_lod)
        assert(Blender.Object.Get("Cube_LOD1").parent == b_lod)
        # test stuff
        check_lodnode(nif_import.root_blocks[0])
        # export
        nif_export = self.test(
            filename='test/nif/ee2/_lodtest.nif',
            config=dict(game = 'EMPIRE_EARTH_II'),
            selection = ['Cube'])
        # test stuff
        check_lodnode(nif_export.root_blocks[0])

suite = LODTestSuite("lod")
suite.run()

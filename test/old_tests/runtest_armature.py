"""Automated armature test for the blender nif scripts."""

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

class ArmatureTestSuite(TestSuite):

    def run(self):
        self.test_armature_modifier()

    def test_armature_modifier(self):
        """Armature modifier test."""

        def check_armature(root):
            """Check nif hierarchy and armature setup."""
            # TODO
            pass

        # import
        nif_import = self.test(
            filename='test/nif/ee2/lodtest-skinned.nif',
            config=dict(
                IMPORT_SCALE_CORRECTION=1))
        # check hierarchy
        b_arm = Blender.Object.Get("LodTestSkinned")
        b_lod = Blender.Object.Get("Cube")
        b_lod0 = Blender.Object.Get("Cube_LOD0")
        b_lod1 = Blender.Object.Get("Cube_LOD0")
        assert(b_lod0.parent == b_lod)
        assert(b_lod1.parent == b_lod)
        assert(b_lod.parent == b_arm)
        # check that the two lod children have an armature modifier
        assert(b_lod0.modifiers[0].type == Blender.Modifier.Types.ARMATURE)
        assert(b_lod1.modifiers[0].type == Blender.Modifier.Types.ARMATURE)
        # test stuff
        check_armature(nif_import.root_blocks[0])
        # export
        nif_export = self.test(
            filename='test/nif/ee2/_lodtest-skinned.nif',
            config=dict(game = 'EMPIRE_EARTH_II'),
            selection = ['LodTestSkinned'])
        # test stuff
        check_armature(nif_export.root_blocks[0])

suite = ArmatureTestSuite("armature")
suite.run()

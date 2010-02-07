"""Automated controller tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2009, NIF File Format Library and Tools
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

class ControllerTestSuite(TestSuite):

    def run(self):
        self.test_alpha_controller()
        self.test_matcolor_controller()
        self.test_vis_controller()

    def test_alpha_controller(self):
        """Alpha controller test."""
        # import
        nif_import = self.test(
            filename='test/nif/mw/alphactrl.nif')
        b_alphactrl = Blender.Object.Get("AlphaCtrlTest")
        # test stuff
        # export
        nif_export = self.test(
            filename='test/nif/_alphactrl.nif',
            config=dict(EXPORT_VERSION = 'Morrowind'),
            selection = ['AlphaCtrlTest'])
        # test stuff
        alphactrl = nif_export.root_blocks[0].children[0]

    def test_matcolor_controller(self):
        """Material color controller test."""
        # import
        nif_import = self.test(
            filename='test/nif/mw/matcolorctrl.nif')
        b_matcolorctrl = Blender.Object.Get("MatColorCtrlTest")
        # test stuff
        # export
        nif_export = self.test(
            filename='test/nif/_matcolorctrl.nif',
            config=dict(EXPORT_VERSION = 'Morrowind'),
            selection = ['MatColorCtrlTest'])
        # test stuff
        matcolorctrl = nif_export.root_blocks[0].children[0]

    def test_vis_controller(self):
        """Vis controller test."""
        # import
        nif_import = self.test(
            filename='test/nif/mw/visctrl.nif')
        b_cube1 = Blender.Object.Get("VisCtrlCube1")
        b_cube2 = Blender.Object.Get("VisCtrlCube2")
        # test stuff
        # export
        nif_export = self.test(
            filename='test/nif/_visctrl.nif',
            config=dict(EXPORT_VERSION = 'Morrowind'),
            selection = ['VisCtrlCube1', 'VisCtrlCube2'])
        # test stuff
        visctrl = nif_export.root_blocks[0].children[0]

suite = ControllerTestSuite("controller")
suite.run()

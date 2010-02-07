"""Automated controller tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2010, NIF File Format Library and Tools
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
        def check_alpha_controller(root):
            for prop in root.children[0].get_properties():
                if isinstance(prop, NifFormat.NiMaterialProperty):
                    for ctrl in prop.get_controllers():
                        if isinstance(ctrl, NifFormat.NiAlphaController):
                            self.logger.info(
                                "found alpha controller, checking data...")
                            # do we have data?
                            assert(ctrl.data)
                            # correct target?
                            assert(ctrl.target == prop)
                            # check the keys
                            ctrldata = ctrl.data.data
                            assert(ctrldata.num_keys == 11)
                            assert(ctrldata.keys[0].time == 0.0)
                            assert(ctrldata.keys[0].value == 1.0)
                            assert(ctrldata.keys[1].time == 1.0)
                            assert(ctrldata.keys[1].value == 0.5)
                            assert(ctrldata.keys[2].time == 2.0)
                            assert(ctrldata.keys[2].value == 1.0)
                            assert(ctrldata.keys[3].time == 3.0)
                            assert(ctrldata.keys[3].value == 0.5)
                            assert(ctrldata.keys[4].time == 4.0)
                            assert(ctrldata.keys[4].value == 1.0)
                            assert(ctrldata.keys[5].time == 5.0)
                            assert(ctrldata.keys[5].value == 0.5)
                            assert(ctrldata.keys[6].time == 6.0)
                            assert(ctrldata.keys[6].value == 1.0)
                            assert(ctrldata.keys[7].time == 7.0)
                            assert(ctrldata.keys[7].value == 0.5)
                            assert(ctrldata.keys[8].time == 8.0)
                            assert(ctrldata.keys[8].value == 1.0)
                            assert(ctrldata.keys[9].time == 9.0)
                            assert(ctrldata.keys[9].value == 0.5)
                            assert(ctrldata.keys[10].time == 10.0)
                            assert(ctrldata.keys[10].value == 1.0)
                            # done!
                            return
            # catch error when property is not found
            raise ValueError("alpha controller not found")
        # import
        nif_import = self.test(
            filename='test/nif/mw/alphactrl.nif')
        b_alphactrl = Blender.Object.Get("AlphaCtrlTest")
        # test stuff
        check_alpha_controller(nif_import.root_blocks[0])
        # export
        nif_export = self.test(
            filename='test/nif/mw/_alphactrl.nif',
            config=dict(EXPORT_VERSION = 'Morrowind'),
            selection = ['AlphaCtrlTest'])
        # test stuff
        check_alpha_controller(nif_export.root_blocks[0])

    def test_matcolor_controller(self):
        """Material color controller test."""
        # import
        nif_import = self.test(
            filename='test/nif/mw/matcolorctrl.nif')
        b_matcolorctrl = Blender.Object.Get("MatColorCtrlTest")
        # test stuff
        # export
        nif_export = self.test(
            filename='test/nif/mw/_matcolorctrl.nif',
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
            filename='test/nif/mw/_visctrl.nif',
            config=dict(EXPORT_VERSION = 'Morrowind'),
            selection = ['VisCtrlCube1', 'VisCtrlCube2'])
        # test stuff
        visctrl = nif_export.root_blocks[0].children[0]

suite = ControllerTestSuite("controller")
suite.run()

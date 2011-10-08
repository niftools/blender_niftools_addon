"""Automated controller tests for the blender nif scripts."""

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
        # check that material has alpha curve
        self.logger.info("checking blender material alpha curve...")
        b_curve = b_alphactrl.getData(mesh=1).materials[0].ipo[
            Blender.Ipo.MA_ALPHA]
        assert(b_curve)
        assert(len(b_curve.bezierPoints) == 11)
        # test stuff
        check_alpha_controller(nif_import.root_blocks[0])
        # export
        nif_export = self.test(
            filename='test/nif/mw/_alphactrl.nif',
            config=dict(game = 'MORROWIND'),
            selection = ['AlphaCtrlTest'])
        # test stuff
        check_alpha_controller(nif_export.root_blocks[0])

    def test_matcolor_controller(self):
        """Material color controller test."""

        def check_matcolor_controller(root):
            matcolor_ctrl = []
            for prop in root.children[0].get_properties():
                if isinstance(prop, NifFormat.NiMaterialProperty):
                    matcolor_ctrl = [
                        ctrl for ctrl in prop.get_controllers()
                        if isinstance(
                            ctrl, NifFormat.NiMaterialColorController)]
            if not len(matcolor_ctrl) == 3:
                raise ValueError("material color controllers not found")
            self.logger.info(
                "found material controllers, checking data...")
            # do we have data?
            assert(all(ctrl.data for ctrl in matcolor_ctrl))
            # correct target?
            assert(all(ctrl.target == prop for ctrl in matcolor_ctrl))
            # correct color target?
            amb_ctrl, diff_ctrl, spec_ctrl = sorted(
                matcolor_ctrl,
                key=lambda ctrl: ctrl.get_target_color())
            assert(spec_ctrl.get_target_color()
                   == NifFormat.TargetColor.TC_SPECULAR)
            assert(diff_ctrl.get_target_color()
                   == NifFormat.TargetColor.TC_DIFFUSE)
            assert(amb_ctrl.get_target_color()
                   == NifFormat.TargetColor.TC_AMBIENT)
            # check the keys
            assert(spec_ctrl.data.data.num_keys == 2)
            assert(spec_ctrl.data.data.keys[0].time == 0)
            assert(spec_ctrl.data.data.keys[0].value.x == 1)
            assert(spec_ctrl.data.data.keys[0].value.y == 1)
            assert(spec_ctrl.data.data.keys[0].value.z == 1)
            assert(spec_ctrl.data.data.keys[1].time == 4)
            assert(spec_ctrl.data.data.keys[1].value.x == 1)
            assert(spec_ctrl.data.data.keys[1].value.y == 1)
            assert(spec_ctrl.data.data.keys[1].value.z == 1)
            assert(diff_ctrl.data.data.num_keys == 2)
            assert(diff_ctrl.data.data.keys[0].time == 0)
            assert(diff_ctrl.data.data.keys[0].value.x == 1)
            assert(diff_ctrl.data.data.keys[0].value.y == 1)
            assert(diff_ctrl.data.data.keys[0].value.z == 1)
            assert(diff_ctrl.data.data.keys[1].time == 4)
            assert(diff_ctrl.data.data.keys[1].value.x == 1)
            assert(diff_ctrl.data.data.keys[1].value.y == 1)
            assert(diff_ctrl.data.data.keys[1].value.z == 1)
            assert(amb_ctrl.data.data.num_keys == 5)
            assert(amb_ctrl.data.data.keys[0].time == 0)
            assert(amb_ctrl.data.data.keys[0].value.x == 0)
            assert(amb_ctrl.data.data.keys[0].value.y == 0)
            assert(amb_ctrl.data.data.keys[0].value.z == 0)
            assert(amb_ctrl.data.data.keys[1].time == 1)
            assert(amb_ctrl.data.data.keys[1].value.x == 1)
            assert(amb_ctrl.data.data.keys[1].value.y == 0)
            assert(amb_ctrl.data.data.keys[1].value.z == 0)
            assert(amb_ctrl.data.data.keys[2].time == 2)
            assert(amb_ctrl.data.data.keys[2].value.x == 0)
            assert(amb_ctrl.data.data.keys[2].value.y == 1)
            assert(amb_ctrl.data.data.keys[2].value.z == 0)
            assert(amb_ctrl.data.data.keys[3].time == 3)
            assert(amb_ctrl.data.data.keys[3].value.x == 0)
            assert(amb_ctrl.data.data.keys[3].value.y == 0)
            assert(amb_ctrl.data.data.keys[3].value.z == 1)
            assert(amb_ctrl.data.data.keys[4].time == 4)
            assert(amb_ctrl.data.data.keys[4].value.x == 1)
            assert(amb_ctrl.data.data.keys[4].value.y == 1)
            assert(amb_ctrl.data.data.keys[4].value.z == 1)

        # import
        nif_import = self.test(
            filename='test/nif/mw/matcolorctrl.nif')
        b_matcolorctrl = Blender.Object.Get("MatColorCtrlTest")
        # check that material has color curves
        self.logger.info("checking blender material color curves...")
        b_ipo = b_matcolorctrl.getData(mesh=1).materials[0].ipo
        for b_channel in (
            Blender.Ipo.MA_R, Blender.Ipo.MA_G, Blender.Ipo.MA_B):
            b_curve = b_ipo[b_channel]
            assert(b_curve)
            assert(len(b_curve.bezierPoints) == 2)
        for b_channel in (
            Blender.Ipo.MA_SPECR, Blender.Ipo.MA_SPECG, Blender.Ipo.MA_SPECB):
            b_curve = b_ipo[b_channel]
            assert(b_curve)
            assert(len(b_curve.bezierPoints) == 2)
        for b_channel in (
            Blender.Ipo.MA_MIRR, Blender.Ipo.MA_MIRG, Blender.Ipo.MA_MIRB):
            b_curve = b_ipo[b_channel]
            assert(b_curve)
            assert(len(b_curve.bezierPoints) == 5)
        # test stuff
        check_matcolor_controller(nif_import.root_blocks[0])
        # export
        nif_export = self.test(
            filename='test/nif/mw/_matcolorctrl.nif',
            config=dict(game = 'MORROWIND'),
            selection = ['MatColorCtrlTest'])
        # test stuff
        check_matcolor_controller(nif_export.root_blocks[0])

    def test_vis_controller(self):
        """Vis controller test."""

        def check_vis_controller(root):
            all_values = [[0, 1, 0], [1, 0, 1]]
            for child, values in zip(root.children, all_values):
                for ctrl in child.get_controllers():
                    if isinstance(ctrl, NifFormat.NiVisController):
                        break
                else:
                    raise ValueError("vis controller not found")
                self.logger.info(
                    "found vis controller, checking data...")
                assert(ctrl.target == child)
                assert(ctrl.data)
                assert(ctrl.data.num_keys == 3)
                for time, (key, value) in enumerate(zip(ctrl.data.keys, values)):
                    assert(key.value == value)
                    assert(key.time == time)

        # import
        nif_import = self.test(
            filename='test/nif/mw/visctrl.nif')
        b_cube1 = Blender.Object.Get("VisCtrlCube1")
        b_cube2 = Blender.Object.Get("VisCtrlCube2")
        # test stuff
        check_vis_controller(nif_import.root_blocks[0])
        # check that object has layer curve
        self.logger.info("checking blender object layer curve...")
        for b_object in (b_cube1, b_cube2):
            assert(b_object.ipo)
            b_curve = b_object.ipo[Blender.Ipo.OB_LAYER]
            assert(b_curve)
            assert(len(b_curve.bezierPoints) == 3)
        # export
        self.context.scene.setLayers([3, 4]) # make sure both are exported
        nif_export = self.test(
            filename='test/nif/mw/_visctrl.nif',
            config=dict(game = 'MORROWIND'),
            selection = ['VisCtrlCube1', 'VisCtrlCube2'])
        # test stuff
        check_vis_controller(nif_export.root_blocks[0])
        self.layer += 1

suite = ControllerTestSuite("controller")
suite.run()

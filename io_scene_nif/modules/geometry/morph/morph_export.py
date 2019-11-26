"""This module contains helper methods to export geometry morph data."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****
import os

import bpy
from pyffi.formats.egm import EgmFormat
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.obj.block_registry import block_store
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class MorphHelper:

    def __init__(self):
        self.egm_data = None

    def export_morph(self, b_mesh, b_obj, tridata, trishape, vertlist, vertmap):
        # shape key morphing
        key = b_mesh.shape_keys
        if key:
            if len(key.key_blocks) > 1:
                # yes, there is a key object attached
                # export as egm, or as morph_data?
                if key.key_blocks[1].name.startswith("EGM"):
                    # egm export!
                    self.export_egm(key.key_blocks)
                # TODO [animation] pull out to
                elif key.ipo:
                    # regular morph_data export
                    # (there must be a shape ipo)
                    keyipo = key.ipo
                    # check that they are relative shape keys
                    if not key.relative:
                        # XXX if we do "key.relative = True"
                        # XXX would this automatically fix the keys?
                        raise ValueError("Can only export relative shape keys.")

                    # create geometry morph controller
                    morph_ctrl = block_store.create_block("NiGeomMorpherController", keyipo)
                    morph_ctrl.target = trishape
                    morph_ctrl.frequency = 1.0
                    morph_ctrl.phase = 0.0
                    trishape.add_controller(morph_ctrl)
                    ctrl_start = 1000000.0
                    ctrl_stop = -1000000.0
                    ctrl_flags = 0x000c

                    # create geometry morph data
                    morph_data = block_store.create_block("NiMorphData", keyipo)
                    morph_ctrl.data = morph_data
                    morph_data.num_morphs = len(key.key_blocks)
                    morph_data.num_vertices = len(vertlist)
                    morph_data.morphs.update_size()

                    # create interpolators (for newer nif versions)
                    morph_ctrl.num_interpolators = len(key.key_blocks)
                    morph_ctrl.interpolators.update_size()

                    # interpolator weights (for Fallout 3)
                    morph_ctrl.interpolator_weights.update_size()

                    # TODO [morph] some unknowns, bethesda only
                    # TODO [morph] just guessing here, data seems to be zero always
                    morph_ctrl.num_unknown_ints = len(key.key_blocks)
                    morph_ctrl.unknown_ints.update_size()

                    for keyblocknum, keyblock in enumerate(key.key_blocks):
                        # export morphed vertices
                        morph = morph_data.morphs[keyblocknum]
                        morph.frame_name = keyblock.name
                        NifLog.info("Exporting morph {0}: vertices".format(keyblock.name))
                        morph.arg = morph_data.num_vertices
                        morph.vectors.update_size()
                        for b_v_index, (vert_indices, vert) in enumerate(list(zip(vertmap, keyblock.data))):
                            # vertmap check
                            if not vert_indices:
                                continue
                            # copy vertex and assign morph vertex
                            mv = vert.copy()
                            if keyblocknum > 0:
                                mv.x -= b_mesh.vertices[b_v_index].co.x
                                mv.y -= b_mesh.vertices[b_v_index].co.y
                                mv.z -= b_mesh.vertices[b_v_index].co.z
                            for vert_index in vert_indices:
                                morph.vectors[vert_index].x = mv.x
                                morph.vectors[vert_index].y = mv.y
                                morph.vectors[vert_index].z = mv.z

                        # export ipo shape key curve
                        curve = keyipo[keyblock.name]

                        # create interpolator for shape key (needs to be there even if there is no curve)
                        interpol = block_store.create_block("NiFloatInterpolator")
                        interpol.value = 0
                        morph_ctrl.interpolators[keyblocknum] = interpol
                        # fallout 3 stores interpolators inside the interpolator_weights block
                        morph_ctrl.interpolator_weights[keyblocknum].interpolator = interpol

                        # geometry only export has no float data also skip keys that have no curve (such as base key)
                        if NifOp.props.animation == 'GEOM_NIF' or not curve:
                            continue

                        # note: we set data on morph for older nifs and on floatdata for newer nifs
                        # of course only one of these will be actually written to the file
                        NifLog.info("Exporting morph {0}: curve".format(keyblock.name))
                        interpol.data = block_store.create_block("NiFloatData", curve)
                        floatdata = interpol.data.data
                        if curve.getExtrapolation() == "Constant":
                            ctrl_flags = 0x000c
                        elif curve.getExtrapolation() == "Cyclic":
                            ctrl_flags = 0x0008

                        morph.interpolation = NifFormat.KeyType.LINEAR_KEY
                        morph.num_keys = len(curve.getPoints())
                        morph.keys.update_size()

                        floatdata.interpolation = NifFormat.KeyType.LINEAR_KEY
                        floatdata.num_keys = len(curve.getPoints())
                        floatdata.keys.update_size()

                        start = bpy.context.scene.frame_start
                        fps = NifOp.context.scene.render.fps
                        for i, btriple in enumerate(curve.getPoints()):
                            knot = btriple.getPoints()
                            morph.keys[i].arg = morph.interpolation
                            morph.keys[i].time = (knot[0] - start) * fps
                            morph.keys[i].value = curve.evaluate(knot[0])
                            # morph.keys[i].forwardTangent = 0.0 # ?
                            # morph.keys[i].backwardTangent = 0.0 # ?
                            floatdata.keys[i].arg = floatdata.interpolation
                            floatdata.keys[i].time = (knot[0] - start) * fps
                            floatdata.keys[i].value = curve.evaluate(knot[0])
                            # floatdata.keys[i].forwardTangent = 0.0 # ?
                            # floatdata.keys[i].backwardTangent = 0.0 # ?
                            ctrl_start = min(ctrl_start, morph.keys[i].time)
                            ctrl_stop = max(ctrl_stop, morph.keys[i].time)
                    morph_ctrl.flags = ctrl_flags
                    morph_ctrl.start_time = ctrl_start
                    morph_ctrl.stop_time = ctrl_stop

                    # fix data consistency type
                    tridata.consistency_flags = b_obj.niftools.consistency_flags

    def export_egm(self, key_blocks):
        self.egm_data = EgmFormat.Data(num_vertices=len(key_blocks[0].data))
        for key_block in key_blocks:
            if key_block.name.startswith("EGM SYM"):
                morph = self.egm_data.add_sym_morph()
            elif key_block.name.startswith("EGM ASYM"):
                morph = self.egm_data.add_asym_morph()
            else:
                continue
            NifLog.info("Exporting morph %s to egm" % key_block.name)
            relative_vertices = []

            # note: key_blocks[0] is base key
            for vert, key_vert in zip(key_blocks[0].data, key_block.data):
                relative_vertices.append(key_vert - vert)
            morph.set_relative_vertices(relative_vertices)

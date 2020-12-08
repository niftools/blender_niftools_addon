"""This script contains classes to help import n_morph animations."""

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

from pyffi.formats.nif import NifFormat
from pyffi.formats.egm import EgmFormat

from io_scene_niftools.modules.nif_export.animation import Animation
from io_scene_niftools.utils.singleton import EGMData

from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


class MorphAnimation(Animation):

    def __init__(self):
        super().__init__()
        EGMData.data = None

    def export_morph(self, b_mesh, n_trishape, vertmap):
        # shape b_key morphing
        b_key = b_mesh.shape_keys
        if b_key and len(b_key.key_blocks) > 1:
            
            # yes, there is a b_key object attached
            # export as egm, or as morph_data?
            if b_key.key_blocks[1].name.startswith("EGM"):
                # egm export!
                self.export_egm(b_key.key_blocks)
            elif b_key.animation_data:
                self.export_morph_animation(b_mesh, b_key, n_trishape, vertmap)

    def export_egm(self, key_blocks):
        EGMData.data = EgmFormat.Data(num_vertices=len(key_blocks[0].data))
        for key_block in key_blocks:
            if key_block.name.startswith("EGM SYM"):
                morph = EGMData.data.add_sym_morph()
            elif key_block.name.startswith("EGM ASYM"):
                morph = EGMData.data.add_asym_morph()
            else:
                continue
            NifLog.info(f"Exporting morph {key_block.name} to egm")
            relative_vertices = []

            # note: key_blocks[0] is base b_key
            for base_vert, key_vert in zip(key_blocks[0].data, key_block.data):
                relative_vertices.append(key_vert.co - base_vert.co)
            morph.set_relative_vertices(relative_vertices)

    def export_morph_animation(self, b_mesh, b_key, n_trishape, vertmap):
        
        # regular morph_data export
        b_shape_action = self.get_active_action(b_key)
        
        # create geometry morph controller
        morph_ctrl = block_store.create_block("NiGeomMorpherController", b_shape_action)
        morph_ctrl.target = n_trishape
        n_trishape.add_controller(morph_ctrl)
        self.set_flags_and_timing(morph_ctrl, b_shape_action.fcurves, *b_shape_action.frame_range)

        # create geometry n_morph data
        morph_data = block_store.create_block("NiMorphData", b_shape_action)
        morph_ctrl.data = morph_data
        morph_data.num_morphs = len(b_key.key_blocks)
        morph_data.num_vertices = n_trishape.data.num_vertices
        morph_data.morphs.update_size()

        # create interpolators (for newer nif versions)
        morph_ctrl.num_interpolators = len(b_key.key_blocks)
        morph_ctrl.interpolators.update_size()

        # interpolator weights (for Fallout 3)
        morph_ctrl.interpolator_weights.update_size()
        # TODO [morph] some unknowns, bethesda only
        # TODO [morph] just guessing here, data seems to be zero always
        morph_ctrl.num_unknown_ints = len(b_key.key_blocks)
        morph_ctrl.unknown_ints.update_size()
        for key_block_num, key_block in enumerate(b_key.key_blocks):
            # export morphed vertices
            n_morph = morph_data.morphs[key_block_num]
            n_morph.frame_name = key_block.name
            NifLog.info(f"Exporting n_morph {key_block.name}: vertices")
            n_morph.arg = morph_data.num_vertices
            n_morph.vectors.update_size()
            for b_v_index, (n_v_indices, b_vert) in enumerate(list(zip(vertmap, key_block.data))):
                # see if this b_vert is used in the nif
                if not n_v_indices:
                    continue
                # copy blender shapekey vertex
                mv = b_vert.co.copy()
                # make the consecutive keys relative to base shapekey
                if key_block_num > 0:
                    mv.x -= b_mesh.vertices[b_v_index].co.x
                    mv.y -= b_mesh.vertices[b_v_index].co.y
                    mv.z -= b_mesh.vertices[b_v_index].co.z
                # update nif morph vectors
                for n_v_index in n_v_indices:
                    n_morph.vectors[n_v_index].x = mv.x
                    n_morph.vectors[n_v_index].y = mv.y
                    n_morph.vectors[n_v_index].z = mv.z

            # create interpolator for shape b_key (needs to be there even if there is no fcu)
            interpol = block_store.create_block("NiFloatInterpolator")
            interpol.value = 0
            morph_ctrl.interpolators[key_block_num] = interpol

            # fallout 3 stores interpolators inside the interpolator_weights block
            morph_ctrl.interpolator_weights[key_block_num].interpolator = interpol

            # geometry only export has no float data also skip keys that have no fcu (such as base b_key)
            if NifOp.props.animation == 'GEOM_NIF' or not b_shape_action.fcurves:
                continue
            
            # find fcurve that animates this shapekey's influence
            # TODO: Does this need f-strings, too?
            b_dtype = 'key_blocks["{}"].value'.format(key_block.name)
            fcurves = [fcu for fcu in b_shape_action.fcurves if b_dtype in fcu.data_path]
            if not fcurves:
                continue
            fcu = fcurves[0]
            NifLog.info(f"Exporting n_morph {key_block.name}: fcu")
            interpol.data = block_store.create_block("NiFloatData", fcu)
            n_floatdata = interpol.data.data
            # note: we set data on n_morph for older nifs and on floatdata for newer nifs
            # of course only one of these will be actually written to the file
            for n_data in (n_morph, n_floatdata):
                n_data.interpolation = NifFormat.KeyType.LINEAR_KEY
                n_data.num_keys = len(fcurves[0].keyframe_points)
                n_data.keys.update_size()

            for i, b_keyframe in enumerate(fcurves[0].keyframe_points):
                frame, value = b_keyframe.co
                t = frame / self.fps
                for n_data in (n_morph, n_floatdata):
                    n_data.keys[i].arg = n_morph.interpolation
                    n_data.keys[i].time = t
                    n_data.keys[i].value = value
                    # n_data.keys[i].forwardTangent = 0.0 # ?
                    # n_data.keys[i].backwardTangent = 0.0 # ?

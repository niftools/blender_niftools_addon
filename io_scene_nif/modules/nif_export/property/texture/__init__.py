"""This script contains helper methods to export textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

import bpy
from io_scene_nif.modules.nif_export.animation.texture import TextureAnimation
from io_scene_nif.modules.nif_export.property import texture
from io_scene_nif.modules.nif_export.property.texture.writer import TextureWriter
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_logging import NifLog


class TextureSlotManager:

    def __init__(self):
        self.dict_mesh_uvlayers = []
        self.texture_writer = TextureWriter()
        self.texture_anim = TextureAnimation()
        self.b_mat = None

        # todo [texture] refactor texture grabbing to use the dict below
        self.slots = {}
        self._reset_fields()
        self.b_diffuse_slot = None
        self.b_glow_slot = None
        self.b_bump_slot = None
        self.b_normal_slot = None
        self.b_gloss_slot = None
        self.b_dark_slot = None
        self.b_detail_slot = None
        self.b_decal_0_slot = None
        self.b_ref_slot = None
        self.has_alpha_texture = False

    def _reset_fields(self):
        self.b_diffuse_slot = None
        self.b_glow_slot = None
        self.b_bump_slot = None
        self.b_normal_slot = None
        self.b_gloss_slot = None
        self.b_dark_slot = None
        self.b_detail_slot = None
        self.b_decal_0_slot = None
        self.b_ref_slot = None
        self.has_alpha_texture = False
        self.slots = {
            "Diffuse": None,
            "Dark": None,
            "Emit": None,
            "Glow": None,
            "Gloss": None,
            "Specular": None,
            "Normal": None,
            "Bump": None,
            "Detail": None,
            "Decal0": None,
            "Decal1": None,
            "Decal2": None,
        }

    @staticmethod
    def get_used_textslots(b_mat):
        used_slots = []
        if b_mat is not None and b_mat.use_nodes:
            used_slots = [node for node in b_mat.node_tree.nodes if isinstance(node, bpy.types.ShaderNodeTexImage)]
        return used_slots

    @staticmethod
    def get_uv_layers(b_mat):
        used_uvlayers = set()
        texture_slots = TextureSlotManager.get_used_textslots(b_mat)
        for slot in texture_slots:
            used_uvlayers.add(slot.uv_layer)
        return used_uvlayers

    def determine_texture_types(self, b_mat):
        """Checks all texture nodes of a material and checks their labels for relevant texture cues.
        Stores all slots as class properties."""
        self.b_mat = b_mat
        self._reset_fields()

        for b_texture_node in self.get_used_textslots(b_mat):
            NifLog.debug(f"Found node {b_texture_node.name} of type {b_texture_node.label}")

            # todo [texture] check which node slot is connected to b_texture_node's vector input
            # # check REFL-mapped textures (used for "NiTextureEffect" materials)
            # if b_texture_node.texture_coords == 'REFLECTION':
            #     if not b_texture_node.use_map_color_diffuse:
            #         # it should map to colour
            #         raise util_math.NifError(
            #             "Non-COL-mapped reflection texture in mesh '%s', material '%s', these cannot be exported to NIF.\n"
            #             "Either delete all non-COL-mapped reflection textures, or in the Shading Panel, \n"
            #             "under Material Buttons, set texture 'Map To' to 'COL'." % (b_mat.name, b_mat.name))
            #     if b_texture_node.blend_type != 'ADD':
            #         # it should have "ADD" blending mode
            #         NifLog.warn("Reflection texture should have blending mode 'Add'"
            #                     " on texture in mesh '{0}', material '{1}').".format(b_mat.name, b_mat.name))
            #     # an envmap image should have an empty... don't care
            #     self.b_ref_slot = b_texture_node
            #
            # # check UV-mapped textures
            # elif b_texture_node.texture_coords == 'UV':

            # go over all slots
            for slot_name in self.slots.keys():
                if slot_name in b_texture_node.label:
                    # slot has already been populated
                    if self.slots[slot_name]:
                        raise util_math.NifError(f"Multiple {slot_name} textures in material '{b_mat.name}''.\n"
                                                 f"Make sure there is only one texture node labeled as '{slot_name}'")
                    # it's a new slot so store it
                    self.slots[slot_name] = b_texture_node
                #     break
                #
                # # unsupported texture type
                # else:
                #     raise util_math.NifError(f"Do not know how to export texture node '{b_texture_node.name}' in material '{b_mat.name}'."
                #                              f"Delete it or change its label.")
            #
            # # nif only support UV-mapped textures
            # else:
            #     NifLog.warn("Non-UV texture in mesh '{0}', material '{1}'.\n"
            #                 "Either delete all non-UV textures or create a UV map for every texture associated "
            #                 "with selected object and run the script again.".
            #                 format(b_mat.name, b_mat.name))

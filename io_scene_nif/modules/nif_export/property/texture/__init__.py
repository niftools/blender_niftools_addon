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
        self.slots = {
            "Diffuse": None,
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

            # todo [texture] refactor this to loop over self.slots
            if True:
                # # update set of uv layers that must be exported
                # if b_texture_node.uv_layer not in self.dict_mesh_uvlayers:
                #     self.dict_mesh_uvlayers.append(b_texture_node.uv_layer)

                #
                # # check if alpha channel is enabled for this texture
                # if b_texture_node.use_map_alpha:
                #     self.has_alpha_texture = True

                # glow tex
                if "Emit" in b_texture_node.label:
                    # multi-check
                    if self.b_glow_slot:
                        raise util_math.NifError("Multiple emissive textures in mesh '{0}', material '{1}''.\n"
                                                 "Make sure there is only one texture set as Influence > emit".
                                                 format(b_mat.name, b_mat.name))
                    self.b_glow_slot = b_texture_node

                # specular
                elif "Specular" in b_texture_node.label:
                    # multi-check
                    if self.b_gloss_slot:
                        raise util_math.NifError("Multiple specular gloss textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > specular".
                                                 format(b_mat.name, b_mat.name))
                    # got the gloss map
                    self.b_gloss_slot = b_texture_node

                # bump map
                elif "Bump" in b_texture_node.label:
                    # multi-check
                    if self.b_bump_slot:
                        raise util_math.NifError("Multiple bump/normal texture in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > normal".
                                                 format(b_mat.name, b_mat.name))
                    self.b_bump_slot = b_texture_node

                # normal map
                elif "Normal" in b_texture_node.label:
                    # multi-check
                    if self.b_normal_slot:
                        raise util_math.NifError("Multiple bump/normal textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > normal".
                                                 format(b_mat.name, b_mat.name))
                    self.b_normal_slot = b_texture_node

                # darken
                elif "Dark" in b_texture_node.label:

                    if self.b_dark_slot:
                        raise util_math.NifError("Multiple Darken textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence > Blend Type > Dark".
                                                 format(b_mat.name, b_mat.name))
                    # got the dark map
                    self.b_dark_slot = b_texture_node

                # diffuse
                elif "Diffuse" in b_texture_node.label:
                    if self.b_diffuse_slot:
                        raise util_math.NifError("Multiple Diffuse textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence > Diffuse > color".
                                                 format(b_mat.name, b_mat.name))
                    self.b_diffuse_slot = b_texture_node

                # detail
                elif "Detail" in b_texture_node.label:
                    if self.b_detail_slot:
                        raise util_math.NifError("Multiple detail textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence Diffuse > color".
                                                 format(b_mat.name, b_mat.name))
                    self.b_detail_slot = b_texture_node

                # Decal 0
                elif "Decal0" in b_texture_node.label:
                    if self.b_decal_0_slot:
                        raise util_math.NifError("Multiple detail textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence Diffuse > color".
                                                 format(b_mat.name, b_mat.name))
                    self.b_decal_0_slot = b_texture_node

                # # reflection
                # elif b_texture_node.use_map_mirror or b_texture_node.use_map_raymir:
                #     # multi-check
                #     if self.b_ref_slot:
                #         raise util_math.NifError("Multiple reflection textures in mesh '{0}', material '{1}'.\n"
                #                                  "Make sure there is only one texture set as Influence > Mirror/Ray Mirror".
                #                                  format(b_mat.name, b_mat.name))
                #     # got the reflection map
                #     # check if alpha channel is enabled for this texture
                #     if b_texture_node.use_map_alpha:
                #         self.has_alpha_texture = True
                #     self.b_ref_slot = b_texture_node

                # unsupported map
                else:
                    raise util_math.NifError("Do not know how to export texture '{0}', in mesh '{1}', material '{2}'.\n"
                                             "Either delete it, or if this texture is to be your base texture.\n"
                                             "Go to the Shading Panel Material Buttons, and set texture 'Map To' to 'COL'.".
                                             format(b_texture_node.name, b_mat.name, b_mat.name))
            #
            # # nif only support UV-mapped textures
            # else:
            #     NifLog.warn("Non-UV texture in mesh '{0}', material '{1}'.\n"
            #                 "Either delete all non-UV textures or create a UV map for every texture associated "
            #                 "with selected object and run the script again.".
            #                 format(b_mat.name, b_mat.name))

    def has_diffuse_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.b_diffuse_slot is not None

        for b_texture_node in self.get_used_textslots(b_mat):
            if b_texture_node.use_map_color_diffuse:
                self.b_diffuse_slot = b_texture_node

        return self.b_diffuse_slot

    def has_glow_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.b_glow_slot is not None

        for b_texture_node in self.get_used_textslots(b_mat):
            if b_texture_node.use_map_emit:
                self.b_glow_slot = b_texture_node
        return self.b_glow_slot

    def has_bumpmap_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.b_bump_slot is not None

        for b_texture_node in self.get_used_textslots(b_mat):
            if b_texture_node.texture.use_normal_map is False and b_texture_node.use_map_color_diffuse is False:
                self.b_bump_slot = b_texture_node
        return self.b_bump_slot

    def has_gloss_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.b_gloss_slot is not None

        for b_texture_node in self.get_used_textslots(b_mat):
            if b_texture_node.use_map_color_spec:
                self.b_gloss_slot = b_texture_node
                return True
        return True

    def has_normalmap_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.b_normal_slot is not None

        for b_texture_node in self.get_used_textslots(b_mat):
            if b_texture_node.use_map_color_diffuse is False and b_texture_node.texture.use_normal_map and b_texture_node.use_map_normal:
                self.b_normal_slot = b_texture_node
                return True
        return False

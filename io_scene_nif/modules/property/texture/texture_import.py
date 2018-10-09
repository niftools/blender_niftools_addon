"""This script contains helper methods to import textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided
#   with the distribution.
# 
# * Neither the name of the NIF File Format Library and Tools
#   project nor the names of its contributors may be used to endorse
#   or promote products derived from this software without specific
#   prior written permission.
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

from io_scene_nif.modules.geometry.mesh.vertex_import import Vertex
from io_scene_nif.modules.property.texture.texture_loader import TextureLoader
from io_scene_nif.utility.nif_logging import NifLog


class TextureSlots:

    def __init__(self):
        self.texture_loader = TextureLoader()

    def create_texture_slot(self, b_mat, image_texture):
        b_mat_texslot = b_mat.texture_slots.add()
        try:
            b_mat_texslot.texture = self.texture_loader.import_texture_source(image_texture.source)
        except:
            b_mat_texslot.texture = self.texture_loader.import_texture_source(image_texture)
        b_mat_texslot.use = True

        # Influence mapping

        # Mapping
        b_mat_texslot.texture_coords = 'UV'
        try:
            b_mat_texslot.uv_layer = Vertex.get_uv_layer_name(image_texture.uv_set)
        except:
            b_mat_texslot.uv_layer = Vertex.get_uv_layer_name(0)

        return b_mat_texslot

    def update_diffuse_slot(self, b_mat_texslot):
        # Influence mapping
        b_mat_texslot.texture.use_alpha = False

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = True
        b_mat_texslot.use_map_color_diffuse = False

    def update_bump_slot(self, b_mat_texslot):
        # Influence mapping
        b_mat_texslot.texture.use_normal_map = False  # causes artifacts otherwise.

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = False
        b_mat_texslot.use_map_normal = True
        b_mat_texslot.use_map_alpha = False

    def update_normal_slot(self, b_mat_texslot):
        # Influence mapping
        b_mat_texslot.texture.use_normal_map = True  # causes artifacts otherwise.

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = False
        b_mat_texslot.use_map_normal = True
        b_mat_texslot.use_map_alpha = False

    def update_glow_slot(self, b_mat_texslot):
        # Influence mapping
        b_mat_texslot.texture.use_alpha = False

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = False
        b_mat_texslot.use_map_emit = True

    def update_gloss_slot(self, b_mat_texslot):
        # Influence mapping
        b_mat_texslot.texture.use_alpha = False

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = False
        b_mat_texslot.use_map_specular = True
        b_mat_texslot.use_map_color_spec = True

    def update_decal_slot(self, b_mat_texslot):
        # self.update_decal_slot(b_mat_texslot)
        # TODO [property][texture] Add support for decal slots
        NifLog.warn("This functionality is not currently supported")
        pass

    def update_decal_slot_0(self, b_mat_texslot):
        self.update_decal_slot(b_mat_texslot)
        # TODO [property][texture] Add support for decal slots

    def update_decal_slot_1(self, b_mat_texslot):
        self.update_decal_slot(b_mat_texslot)
        # TODO [property][texture] Add support for decal slots

    def update_detail_slot(self, b_mat_texslot):
        self.update_decal_slot(b_mat_texslot)
        # TODO [property][texture] Add support for decal slots

    def update_decal_slot_2(self, b_mat_texslot):
        self.update_decal_slot(b_mat_texslot)

    def update_dark_slot(self, b_mat_texslot):
        self.update_decal_slot(b_mat_texslot)
        b_mat_texslot.blend_type = 'DARK'

    def update_reflection_slot(self, b_mat_texslot):
        # Influence mapping

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = True
        b_mat_texslot.use_map_emit = True
        b_mat_texslot.use_map_mirror = True

    def update_environment_slot(self, b_mat_texslot):
        # Influence mapping

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_mat_texslot.use_map_alpha = True

        b_mat_texslot.use_map_color_diffuse = True
        b_mat_texslot.blend_type = 'ADD'

    @staticmethod
    def get_b_blend_type_from_n_apply_mode(n_apply_mode):
        # TODO [material] Check out n_apply_modes
        if n_apply_mode == NifFormat.ApplyMode.APPLY_MODULATE:
            return "MIX"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_REPLACE:
            return "COLOR"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_DECAL:
            return "OVERLAY"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT:
            return "LIGHTEN"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT2:  # used by Oblivion for parallax
            return "MULTIPLY"
        else:
            NifLog.warn("Unknown apply mode (%i) in material, using blend type 'MIX'".format(n_apply_mode))
            return "MIX"

    # TODO [property][texture] move to each texture type
    # fix up vertex colors depending on whether we had textures in the material
    # mbasetex = self.texturehelper.has_base_texture(material)
    # mglowtex = self.texturehelper.has_glow_texture(material)
    # if b_mesh.vertex_colors:
    #     if mbasetex or mglowtex:
    #         # textured material: vertex colors influence lighting
    #         material.use_vertex_color_light = True
    #     else:
    #         # non-textured material: vertex colors incluence color
    #         material.use_vertex_color_paint = True

    # TODO [texture] check to see if the is needed.
    # # if there's a base texture assigned to this material sets it
    # # to be displayed in Blender's 3D view
    # # but only if there are UV coordinates
    # if mbasetex and mbasetex.texture and n_uvco:
    #     imgobj = mbasetex.texture.image
    #     if imgobj:
    #         for b_polyimage_index in f_map:
    #             if b_polyimage_index is None:
    #                 continue
    #             tface = b_mesh.uv_textures.active.data[b_polyimage_index]
    #             # gone in blender 2.5x+?
    #             # f.mode = Blender.Mesh.FaceModes['TEX']
    #             # f.transp = Blender.Mesh.FaceTranspModes['ALPHA']
    #             tface.image = imgobj

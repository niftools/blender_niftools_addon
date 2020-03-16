"""This script contains helper methods to import shader property data."""

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

from abc import ABC

import bpy

from io_scene_nif.modules.nif_import.object.block_registry import block_store
from io_scene_nif.utils.util_logging import NifLog


class BSShader(ABC):

    def __init__(self):
        self.b_mesh = None

    @staticmethod
    def import_uv_offset(b_mat, shader_prop):
        for texture_slot in b_mat.texture_slots:
            if texture_slot:
                texture_slot.offset.x = shader_prop.uv_offset.u
                texture_slot.offset.y = shader_prop.uv_offset.v

    @staticmethod
    def import_uv_scale(b_mat, shader_prop):
        for texture_slot in b_mat.texture_slots:
            if texture_slot:
                texture_slot.scale.x = shader_prop.uv_scale.u
                texture_slot.scale.y = shader_prop.uv_scale.v

    @staticmethod
    def import_clamp(b_mat, shader_prop):
        clamp = shader_prop.texture_clamp_mode
        for texture_slot in b_mat.texture_slots:
            if texture_slot:
                if clamp == 3:
                    texture_slot.texture.image.use_clamp_x = False
                    texture_slot.texture.image.use_clamp_y = False
                if clamp == 2:
                    texture_slot.texture.image.use_clamp_x = False
                    texture_slot.texture.image.use_clamp_y = True
                if clamp == 1:
                    texture_slot.texture.image.use_clamp_x = True
                    texture_slot.texture.image.use_clamp_y = False
                if clamp == 0:
                    texture_slot.texture.image.use_clamp_x = True
                    texture_slot.texture.image.use_clamp_y = True

    @staticmethod
    def set_alpha_bsshader(b_mat, shader_property):
        NifLog.debug("Alpha prop detected")
        b_mat.use_transparency = True
        b_mat.alpha = (1 - shader_property.alpha)
        b_mat.transparency_method = 'Z_TRANSPARENCY'  # enable z-buffered transparency
        return b_mat

    def _find_or_create_material(self):
        b_mats = self.b_mesh.materials
        if len(b_mats) == 0:
            b_mat = bpy.data.materials.new("")
            self.b_mesh.materials.append(b_mat)
            NifLog.debug("Created placeholder material to store properties in {0}".format(b_mat))
        else:
            b_mat = self.b_mesh.materials[0]
            NifLog.debug("Reusing existing material {0} to store additional properties in {0}".format(b_mat))
        return b_mat

    def create_material_name(self, bs_shader_property):
        name = block_store.import_name(bs_shader_property)
        if name is None:
            name = (self._n_block.name.decode() + "_nt_mat")
        b_mat = bpy.data.materials.new(name)
        self._b_mesh.materials.append(b_mat)
        return b_mat

    @staticmethod
    def import_flags(b_mat, flags):
        for name in flags._names:
            sf_index = flags._names.index(name)
            if flags._items[sf_index]._value == 1:
                b_mat.niftools_shader[name] = True

    # def get_bsshader_hash(self, bs_shader_property, bs_effect_shader_property):
    #     return (bs_shader_property.get_hash()[1:] if bs_shader_property else None,  # skip first element, which is name
    #             bs_effect_shader_property.get_hash() if bs_effect_shader_property else None)

    # TODO [shader] Move move out when nolonger required to reference
    # def find_bsshaderproperty(self, n_block):
    #     # bethesda shader
    #     bsshaderproperty = util_math.find_property(n_block, NifFormat.BSShaderPPLightingProperty)
    #     if not bsshaderproperty:
    #         bsshaderproperty = util_math.find_property(n_block, NifFormat.BSLightingShaderProperty)
    #
    #     if bsshaderproperty:
    #         for textureslot in bsshaderproperty.texture_set.textures:
    #             if textureslot:
    #                 self.bsShaderProperty1st = bsshaderproperty
    #                 break
    #         else:
    #             bsshaderproperty = self.bsShaderProperty1st
    #     return bsshaderproperty

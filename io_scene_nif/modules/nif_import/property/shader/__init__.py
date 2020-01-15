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
import bpy
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.modules.nif_import.property.texture import TextureSlotManager
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_logging import NifLog


class BSShader:

    def __init__(self):
        self.dict_materials = {}
        self.texturehelper = TextureSlotManager()

    @staticmethod
    def import_shader_types(b_obj, b_prop):
        if isinstance(b_prop, NifFormat.BSShaderPPLightingProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSShaderPPLightingProperty'
            sf_type = NifFormat.BSShaderType._enumvalues.index(b_prop.shader_type)
            b_obj.niftools_shader.bsspplp_shaderobjtype = NifFormat.BSShaderType._enumkeys[sf_type]
            for b_flag_name in b_prop.shader_flags._names:
                sf_index = b_prop.shader_flags._names.index(b_flag_name)
                if b_prop.shader_flags._items[sf_index]._value == 1:
                    b_obj.niftools_shader[b_flag_name] = True

        if isinstance(b_prop, NifFormat.BSLightingShaderProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSLightingShaderProperty'
            sf_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues.index(b_prop.skyrim_shader_type)
            b_obj.niftools_shader.bslsp_shaderobjtype = NifFormat.BSLightingShaderPropertyShaderType._enumkeys[sf_type]
            BSShader.import_shader_flags(b_obj, b_prop)

        elif isinstance(b_prop, NifFormat.BSEffectShaderProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSEffectShaderProperty'
            b_obj.niftools_shader.bslsp_shaderobjtype = 'Default'
            BSShader.import_shader_flags(b_obj, b_prop)

    @staticmethod
    def import_shader_flags(b_obj, b_prop):
        for b_flag_name_1 in b_prop.shader_flags_1._names:
            sf_index = b_prop.shader_flags_1._names.index(b_flag_name_1)
            if b_prop.shader_flags_1._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name_1] = True

        for b_flag_name_2 in b_prop.shader_flags_2._names:
            sf_index = b_prop.shader_flags_2._names.index(b_flag_name_2)
            if b_prop.shader_flags_2._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name_2] = True

    def import_bsshader_material(self, bs_shader_property, bs_effect_shader_property, n_alpha_prop):
        material_hash = self.get_bsshader_hash(bs_shader_property, bs_effect_shader_property)
        try:
            return self.dict_materials[material_hash]
        except KeyError:
            pass

        # name unique material
        name = block_store.import_name(bs_shader_property)
        if not name:
            name = bpy.context.scene.objects.active + "_nt_mat"
        b_mat = bpy.data.materials.new(name)

        if bs_shader_property:
            self.texturehelper.import_bsshaderproperty_textures(b_mat, bs_shader_property)
        if bs_effect_shader_property:
            self.texturehelper.import_bseffectshaderproperty_textures(b_mat, bs_effect_shader_property)

        # shader based properties
        if bs_shader_property:

            # Diffuse color
            if bs_shader_property.skin_tint_color:
                b_mat.diffuse_color.r = bs_shader_property.skin_tint_color.r
                b_mat.diffuse_color.g = bs_shader_property.skin_tint_color.g
                b_mat.diffuse_color.b = bs_shader_property.skin_tint_color.b
                b_mat.diffuse_intensity = 1.0

            if (b_mat.diffuse_color.r + b_mat.diffuse_color.g + b_mat.diffuse_color.g) == 0:
                b_mat.diffuse_color.r = bs_shader_property.hair_tint_color.r
                b_mat.diffuse_color.g = bs_shader_property.hair_tint_color.g
                b_mat.diffuse_color.b = bs_shader_property.hair_tint_color.b
                b_mat.diffuse_intensity = 1.0

            # Emissive
            b_mat.niftools.emissive_color.r = bs_shader_property.emissive_color.r
            b_mat.niftools.emissive_color.g = bs_shader_property.emissive_color.g
            b_mat.niftools.emissive_color.b = bs_shader_property.emissive_color.b
            b_mat.emit = bs_shader_property.emissive_multiple

            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha_bsshader(b_mat, bs_shader_property, n_alpha_prop)

            # gloss
            b_mat.specular_hardness = bs_shader_property.glossiness

            # Specular color
            b_mat.specular_color.r = bs_shader_property.specular_color.r
            b_mat.specular_color.g = bs_shader_property.specular_color.g
            b_mat.specular_color.b = bs_shader_property.specular_color.b
            b_mat.specular_intensity = bs_shader_property.specular_strength

            # lighting effect
            b_mat.niftools.lightingeffect1 = bs_shader_property.lighting_effect_1
            b_mat.niftools.lightingeffect2 = bs_shader_property.lighting_effect_2

        if bs_effect_shader_property:
            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha_bsshader(b_mat, bs_shader_property, n_alpha_prop)

            if bs_effect_shader_property.emissive_color:
                b_mat.niftools.emissive_color.r = bs_effect_shader_property.emissive_color.r
                b_mat.niftools.emissive_color.g = bs_effect_shader_property.emissive_color.g
                b_mat.niftools.emissive_color.b = bs_effect_shader_property.emissive_color.b
                b_mat.niftools.emissive_alpha = bs_effect_shader_property.emissive_color.a
                b_mat.emit = bs_effect_shader_property.emissive_multiple
            b_mat.niftools_alpha.textureflag = bs_effect_shader_property.controller.flags

    def set_alpha_bsshader(self, b_mat, shader_property):
        NifLog.debug("Alpha prop detected")
        b_mat.use_transparency = True
        b_mat.alpha = (1 - shader_property.alpha)
        b_mat.transparency_method = 'Z_TRANSPARENCY'  # enable z-buffered transparency
        return b_mat

    def get_bsshader_hash(self, bs_shader_property, bs_effect_shader_property):
        return (bs_shader_property.get_hash()[1:] if bs_shader_property else None,  # skip first element, which is name
                bs_effect_shader_property.get_hash() if bs_effect_shader_property else None)

    # TODO [shader] Move move out when nolonger required to reference
    def find_bsshaderproperty(self, n_block):
        # bethesda shader
        bsshaderproperty = nif_utils.find_property(n_block, NifFormat.BSShaderPPLightingProperty)
        if not bsshaderproperty:
            bsshaderproperty = nif_utils.find_property(n_block, NifFormat.BSLightingShaderProperty)

        if bsshaderproperty:
            for textureslot in bsshaderproperty.texture_set.textures:
                if textureslot:
                    self.bsShaderProperty1st = bsshaderproperty
                    break
            else:
                bsshaderproperty = self.bsShaderProperty1st
        return bsshaderproperty

    def import_uv_offset(b_mat, shader_prop):
        for texture_slot in b_mat.texture_slots:
            if texture_slot:
                texture_slot.offset.x = shader_prop.uv_offset.u
                texture_slot.offset.y = shader_prop.uv_offset.v

    def import_uv_scale(b_mat, shader_prop):
        for texture_slot in b_mat.texture_slots:
            if texture_slot:
                texture_slot.scale.x = shader_prop.uv_scale.u
                texture_slot.scale.y = shader_prop.uv_scale.v

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

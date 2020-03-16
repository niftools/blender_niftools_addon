"""This script contains helper methods to import BSShaderProperty based properties."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules.nif_import.property.material import Material
from io_scene_nif.modules.nif_import.property.shader import BSShader
from io_scene_nif.modules.nif_import.property.texture.types.bsshadertexture import BSShaderTexture


class BSShaderPropertyProcessor(BSShader):
    """
    <niobject name="HairShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#BETHESDA#">Bethesda-specific property.
    <niobject name="DistantLODShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#BETHESDA#">Bethesda-specific property.
    <niobject name="TallGrassShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#BETHESDA#">Bethesda-specific property.

    <niobject name="BSDistantTreeShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#FO3_AND_LATER#">Bethesda-specific property.
    <niobject name="VolumetricFogShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#FO3_AND_LATER#">Bethesda-specific property.
    <niobject name="WaterShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#FO3_AND_LATER#">Bethesda-specific property. Found in Fallout3

    <niobject name="BSLightingShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#SKY_AND_LATER#">Bethesda shader property for Skyrim and later.
    <niobject name="BSEffectShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#SKY_AND_LATER#">Bethesda effect shader property for Skyrim and later.
    <niobject name="BSWaterShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#SKY_AND_LATER#">Skyrim water shader property, different from "WaterShaderProperty" seen in Fallout.
    <niobject name="BSSkyShaderProperty" inherit="BSShaderProperty" module="BSMain" versions="#SKY_AND_LATER#">Skyrim Sky shader block.
    """

    __instance = None
    _b_mesh = None
    _n_block = None

    @property
    def b_mesh(self):
        return self._b_mesh

    @b_mesh.setter
    def b_mesh(self, value):
        self._b_mesh = value

    @property
    def n_block(self):
        return self._n_block

    @n_block.setter
    def n_block(self, value):
        self._n_block = value

    def __init__(self):
        """ Virtually private constructor. """
        if BSShaderPropertyProcessor.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            super().__init__()
            BSShaderPropertyProcessor.__instance = self
            self.texturehelper = BSShaderTexture.get()

    @staticmethod
    def get():
        """ Static access method. """
        if not BSShaderPropertyProcessor.__instance:
            BSShaderPropertyProcessor()
        return BSShaderPropertyProcessor.__instance

    def register_bsproperty(self, processor):
        processor.register(NifFormat.BSLightingShaderProperty, self.import_bs_lighting_shader_property)
        processor.register(NifFormat.BSEffectShaderProperty, self.import_bs_effect_shader_property)

    def import_bs_lighting_shader_property(self, bs_shader_property):
        b_mat = self.create_material_name(bs_shader_property)

        # Shader Flags
        b_shader = b_mat.niftools_shader
        b_shader.bs_shadertype = 'BSLightingShaderProperty'

        shader_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues.index(bs_shader_property.skyrim_shader_type)
        b_shader.bslsp_shaderobjtype = NifFormat.BSLightingShaderPropertyShaderType._enumkeys[shader_type]

        self.import_shader_flags(b_mat, bs_shader_property)

        # Textures
        self.texturehelper.import_bsshaderproperty_textureset(b_mat, bs_shader_property)
        if hasattr(bs_shader_property, 'texture_clamp_mode'):
            self.import_clamp(b_mat, bs_shader_property)

        if hasattr(bs_shader_property, 'uv_offset'):
            self.import_uv_offset(b_mat, bs_shader_property)

        if hasattr(bs_shader_property, 'uv_scale'):
            self.import_uv_scale(b_mat, bs_shader_property)

        # Diffuse color
        if bs_shader_property.skin_tint_color:
            Material.import_material_diffuse(b_mat, bs_shader_property.skin_tint_color)

        if (b_mat.diffuse_color.r + b_mat.diffuse_color.g + b_mat.diffuse_color.g) == 0:
            Material.import_material_diffuse(b_mat, bs_shader_property.hair_tint_color)

        # TODO [material][b_shader][property] Handle nialphaproperty node lookup
        # # Alpha
        # if n_alpha_prop:
        #     b_mat = self.set_alpha_bsshader(b_mat, bs_shader_property)

        # gloss
        Material.import_material_gloss(b_mat, bs_shader_property.glossiness)

        # Specular color
        Material.import_material_specular(b_mat, bs_shader_property.specular_color)
        b_mat.specular_intensity = bs_shader_property.specular_strength

        # lighting effect
        b_mat.niftools.lightingeffect1 = bs_shader_property.lighting_effect_1
        b_mat.niftools.lightingeffect2 = bs_shader_property.lighting_effect_2

    def import_bs_effect_shader_property(self, bs_effect_shader_property):
        # update material material name
        b_mat = self.create_material_name(bs_effect_shader_property)

        shader = b_mat.niftools_shader
        shader.bs_shadertype = 'BSEffectShaderProperty'
        shader.bslsp_shaderobjtype = 'Default'
        self.import_shader_flags(b_mat, bs_effect_shader_property)

        self.texturehelper.import_bseffectshaderproperty_textures(b_mat, bs_effect_shader_property)

        if hasattr(bs_effect_shader_property, 'uv_offset'):
            self.import_uv_offset(b_mat, bs_effect_shader_property)

        if hasattr(bs_effect_shader_property, 'uv_scale'):
            self.import_uv_scale(b_mat, bs_effect_shader_property)

        # TODO [material][shader][property] Handle nialphaproperty node lookup
        # # Alpha
        # if n_alpha_prop:
        #     b_mat = self.set_alpha_bsshader(b_mat, bs_effect_shader_property)

        # Emissive
        Material.import_material_emissive(bs_effect_shader_property.emissive_color)
        b_mat.emit = bs_effect_shader_property.emissive_multiple

        if bs_effect_shader_property.emissive_color:
            Material.import_material_emissive(bs_effect_shader_property.emissive_color)
            b_mat.niftools.emissive_alpha = bs_effect_shader_property.emissive_color.a
            b_mat.emit = bs_effect_shader_property.emissive_multiple

        b_mat.niftools_alpha.textureflag = bs_effect_shader_property.controller.flags

    def import_shader_flags(self, b_mat, b_prop):
        flags_1 = b_prop.shader_flags_1
        self.import_flags(b_mat, flags_1)

        flag_2 = b_prop.shader_flags_2
        self.import_flags(b_mat, flag_2)

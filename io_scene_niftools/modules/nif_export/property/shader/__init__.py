"""This script contains helper methods to export shader property data."""

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

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export.property.texture.types.bsshadertexture import BSShaderTexture
from io_scene_niftools.utils import math
from io_scene_niftools.utils.consts import FLOAT_MAX


class BSShaderProperty:

    def __init__(self):
        self.texturehelper = BSShaderTexture.get()

    def export_bs_shader_property(self, b_mat=None):
        """Export a Bethesda shader property block."""
        if b_mat.niftools_shader.bs_shadertype == 'None':
            raise io_scene_niftools.utils.logging.NifError(f"Export version expected shader. No shader applied to mesh '{b_mat}', these cannot be exported to NIF."
                                     f"Set shader before exporting.")

        self.texturehelper.determine_texture_types(b_mat)

        # create new block
        if b_mat.niftools_shader.bs_shadertype == 'BSShaderPPLightingProperty':
            bsshader = self.export_bs_shader_pp_lighting_property(b_mat)

        if b_mat.niftools_shader.bs_shadertype == 'BSLightingShaderProperty':
            bsshader = self.export_bs_lighting_shader_property(b_mat)

        if b_mat.niftools_shader.bs_shadertype == 'BSEffectShaderProperty':
            bsshader = self.export_bs_effect_shader_property(b_mat)

        return bsshader

    def export_bs_effect_shader_property(self, b_mat):
        bsshader = NifFormat.BSEffectShaderProperty()

        self.texturehelper.export_bs_effect_shader_prop_textures(bsshader)

        # Alpha
        # TODO [Shader] Alpha property
        # if b_mat.use_transparency:
        #     bsshader.alpha = (1 - b_mat.alpha)

        # Emissive
        bsshader.emissive_color.r = b_mat.niftools.emissive_color.r
        bsshader.emissive_color.g = b_mat.niftools.emissive_color.g
        bsshader.emissive_color.b = b_mat.niftools.emissive_color.b
        bsshader.emissive_color.a = b_mat.niftools.emissive_alpha.v
        # TODO [shader] Expose a emission multiplier value
        # bsshader.emissive_multiple = b_mat.emit

        # Shader Flags
        BSShaderProperty.export_shader_flags(b_mat, bsshader)

        return bsshader

    def export_bs_lighting_shader_property(self, b_mat):
        bsshader = NifFormat.BSLightingShaderProperty()
        b_s_type = NifFormat.BSLightingShaderPropertyShaderType._enumkeys.index(b_mat.niftools_shader.bslsp_shaderobjtype)
        bsshader.skyrim_shader_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues[b_s_type]

        self.texturehelper.export_bs_lighting_shader_prop_textures(bsshader)

        # Diffuse color
        d = b_mat.diffuse_color
        bsshader.skin_tint_color.r = d[0]
        bsshader.skin_tint_color.g = d[1]
        bsshader.skin_tint_color.b = d[2]
        # TODO [shader] expose intensity value
        # b_mat.diffuse_intensity = 1.0

        bsshader.lighting_effect_1 = b_mat.niftools.lightingeffect1
        bsshader.lighting_effect_2 = b_mat.niftools.lightingeffect2

        # Emissive
        e = b_mat.niftools.emissive_color
        bsshader.emissive_color.r = e[0]
        bsshader.emissive_color.g = e[1]
        bsshader.emissive_color.b = e[2]
        # TODO [shader] Expose a emission multiplier value
        # bsshader.emissive_multiple = b_mat.emit

        # gloss
        bsshader.glossiness = 1/b_mat.roughness - 1 if b_mat.roughness != 0 else FLOAT_MAX

        # Specular color
        s = b_mat.specular_color
        bsshader.specular_color.r = s[0]
        bsshader.specular_color.g = s[1]
        bsshader.specular_color.b = s[2]
        bsshader.specular_strength = b_mat.specular_intensity

        # Alpha
        # TODO [Shader] Alpha property
        # if b_mat.use_transparency:
        #     bsshader.alpha = (1 - b_mat.alpha)

        # Shader Flags
        BSShaderProperty.export_shader_flags(b_mat, bsshader)
        return bsshader

    def export_bs_shader_pp_lighting_property(self, b_mat):
        bsshader = NifFormat.BSShaderPPLightingProperty()
        # set shader options
        # TODO: FIXME:
        b_s_type = NifFormat.BSShaderType._enumkeys.index(b_mat.niftools_shader.bsspplp_shaderobjtype)
        bsshader.shader_type = NifFormat.BSShaderType._enumvalues[b_s_type]

        self.texturehelper.export_bs_shader_pp_lighting_prop_textures(bsshader)

        # Shader Flags
        BSShaderProperty.export_shader_flags(b_mat, bsshader)
        return bsshader

    @staticmethod
    def export_shader_flags(b_mat, shader):
        if hasattr(shader, 'shader_flags'):
            flags = shader.shader_flags
            BSShaderProperty.process_flags(b_mat, flags)

        if hasattr(shader, 'shader_flags_1'):
            flags_1 = shader.shader_flags_1
            BSShaderProperty.process_flags(b_mat, flags_1)

        if hasattr(shader, 'shader_flags_2'):
            flags_2 = shader.shader_flags_2
            BSShaderProperty.process_flags(b_mat, flags_2)

        return shader

    @staticmethod
    def process_flags(b_mat, flags):
        b_flag_list = b_mat.niftools_shader.bl_rna.properties.keys()
        for sf_flag in flags._names:
            if sf_flag in b_flag_list:
                b_flag = b_mat.niftools_shader.get(sf_flag)
                if b_flag:
                    sf_flag_index = flags._names.index(sf_flag)
                    flags._items[sf_flag_index]._value = 1

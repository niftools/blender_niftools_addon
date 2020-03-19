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

from io_scene_nif.modules.nif_export.property.texture import TextureWriter, TextureSlotManager
from io_scene_nif.modules.nif_export.property.texture.types.bsshadertexture import BSShaderTexture
from io_scene_nif.utils import util_math


class BSShaderProperty:

    def __init__(self):
        self.texturehelper = BSShaderTexture.get()

    def export_bs_shader_property(self, b_mat=None):
        """Export a Bethesda shader property block."""
        if b_mat.niftools_shader.bs_shadertype == 'None':
            raise util_math.NifError("Export version expected shader. No shader applied to mesh '{0}', these cannot be exported to NIF."
                                     "Set shader before exporting.".format(b_mat))

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

        self.texturehelper.export_bs_effect_shader_property(bsshader)

        # Alpha
        if b_mat.use_transparency:
            bsshader.alpha = (1 - b_mat.alpha)

        # clamp Mode
        bsshader.texture_clamp_mode = 65283

        # Emissive
        bsshader.emissive_color.r = b_mat.niftools.emissive_color.r
        bsshader.emissive_color.g = b_mat.niftools.emissive_color.g
        bsshader.emissive_color.b = b_mat.niftools.emissive_color.b
        bsshader.emissive_color.a = b_mat.niftools.emissive_alpha.v
        bsshader.emissive_multiple = b_mat.emit

        # Shader Flags
        BSShaderProperty.export_shader_flags(b_mat, bsshader)

        return bsshader

    def export_bs_lighting_shader_property(self, b_mat):
        bsshader = NifFormat.BSLightingShaderProperty()
        b_s_type = NifFormat.BSLightingShaderPropertyShaderType._enumkeys.index(b_mat.niftools_shader.bslsp_shaderobjtype)
        bsshader.shader_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues[b_s_type]

        self.texturehelper.export_bs_lighting_shader_property(bsshader)

        # Diffuse color
        bsshader.skin_tint_color.r = b_mat.diffuse_color.r
        bsshader.skin_tint_color.g = b_mat.diffuse_color.g
        bsshader.skin_tint_color.b = b_mat.diffuse_color.b
        # b_mat.diffuse_intensity = 1.0

        bsshader.lighting_effect_1 = b_mat.niftools.lightingeffect1
        bsshader.lighting_effect_2 = b_mat.niftools.lightingeffect2

        # Emissive
        bsshader.emissive_color.r = b_mat.niftools.emissive_color.r
        bsshader.emissive_color.g = b_mat.niftools.emissive_color.g
        bsshader.emissive_color.b = b_mat.niftools.emissive_color.b
        bsshader.emissive_multiple = b_mat.emit

        # gloss
        bsshader.glossiness = b_mat.specular_hardness

        # Specular color
        bsshader.specular_color.r = b_mat.specular_color.r
        bsshader.specular_color.g = b_mat.specular_color.g
        bsshader.specular_color.b = b_mat.specular_color.b
        bsshader.specular_strength = b_mat.specular_intensity

        # Alpha
        if b_mat.use_transparency:
            bsshader.alpha = (1 - b_mat.alpha)

        # Shader Flags
        BSShaderProperty.export_shader_flags(b_mat, bsshader)
        return bsshader

    def export_bs_shader_pp_lighting_property(self, b_mat):
        bsshader = NifFormat.BSShaderPPLightingProperty()
        # set shader options
        # TODO: FIXME:
        b_s_type = NifFormat.BSShaderType._enumkeys.index(b_mat.niftools_shader.bsspplp_shaderobjtype)
        bsshader.shader_type = NifFormat.BSShaderType._enumvalues[b_s_type]

        self.texturehelper.export_bs_shader_pp_lighting_property()

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

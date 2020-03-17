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

from io_scene_nif.modules.nif_export.property.texture import TextureWriter, Texture
from io_scene_nif.utils import util_math


class BSShader:

    def __init__(self):
        self.texturehelper = Texture()

    def export_bs_shader_property(self, b_mat=None):
        """Export a Bethesda shader property block."""
        self.texturehelper.determine_texture_types(b_mat)

        # create new block
        if b_mat.niftools_shader.bs_shadertype == 'BSShaderPPLightingProperty':
            bsshader = NifFormat.BSShaderPPLightingProperty()

            # set shader options
            # TODO: FIXME:
            b_s_type = NifFormat.BSShaderType._enumkeys.index(b_mat.niftools_shader.bsspplp_shaderobjtype)
            bsshader.shader_type = NifFormat.BSShaderType._enumvalues[b_s_type]

            # Shader Flags
            if hasattr(bsshader, 'shader_flags'):
                BSShader.export_shader_flags(b_mat, bsshader)

        if b_mat.niftools_shader.bs_shadertype == 'BSLightingShaderProperty':
            bsshader = NifFormat.BSLightingShaderProperty()
            b_s_type = NifFormat.BSLightingShaderPropertyShaderType._enumkeys.index(b_mat.niftools_shader.bslsp_shaderobjtype)
            bsshader.shader_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues[b_s_type]

            # UV Offset
            if hasattr(bsshader, 'uv_offset'):
                self.export_uv_offset(bsshader)

            # UV Scale
            if hasattr(bsshader, 'uv_scale'):
                self.export_uv_scale(bsshader)

            # Texture Clamping mode
            if not self.texturehelper.base_mtex.texture.image.use_clamp_x:
                wrap_s = 2
            else:
                wrap_s = 0
            if not self.texturehelper.base_mtex.texture.image.use_clamp_y:
                wrap_t = 1
            else:
                wrap_t = 0
            bsshader.texture_clamp_mode = (wrap_s + wrap_t)

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
            if hasattr(bsshader, 'shader_flags_1'):
                self.export_shader_flags(b_mat, bsshader)

        if b_mat.niftools_shader.bs_shadertype == 'BSEffectShaderProperty':
            bsshader = NifFormat.BSEffectShaderProperty()

            # Alpha
            if b_mat.use_transparency:
                bsshader.alpha = (1 - b_mat.alpha)

            # clamp Mode
            bsshader.texture_clamp_mode = 65283

            # Emissive
            bsshader.emissive_color.r = b_mat.niftools.emissive_color.r
            bsshader.emissive_color.g = b_mat.niftools.emissive_color.g
            bsshader.emissive_color.b = b_mat.niftools.emissive_color.b
            bsshader.emissive_color.a = b_mat.niftools.emissive_alpha
            bsshader.emissive_multiple = b_mat.emit

            # Shader Flags
            if hasattr(bsshader, 'shader_flags_1'):
                self.export_shader_flags(b_mat, bsshader)

        if b_mat.niftools_shader.bs_shadertype == 'None':
            raise util_math.NifError("Export version expected shader. No shader applied to mesh '{0}', these cannot be exported to NIF."
                                     "Set shader before exporting.".format(b_mat))
        # set textures
        texset = NifFormat.BSShaderTextureSet()
        bsshader.texture_set = texset
        if self.texturehelper.base_mtex:
            texset.textures[0] = TextureWriter.export_texture_filename(self.texturehelper.base_mtex.texture)
        if self.texturehelper.normal_mtex:
            texset.textures[1] = TextureWriter.export_texture_filename(self.texturehelper.normal_mtex.texture)
        if self.texturehelper.glow_mtex:
            texset.textures[2] = TextureWriter.export_texture_filename(self.texturehelper.glow_mtex.texture)
        if self.texturehelper.detail_mtex:
            texset.textures[3] = TextureWriter.export_texture_filename(self.texturehelper.detail_mtex.texture)

        if b_mat.niftools_shader.bs_shadertype == 'BSLightingShaderProperty':
            texset.num_textures = 9
            texset.textures.update_size()
            if self.texturehelper.detail_mtex:
                texset.textures[6] = TextureWriter.export_texture_filename(self.texturehelper.detail_mtex.texture)
            if self.texturehelper.gloss_mtex:
                texset.textures[7] = TextureWriter.export_texture_filename(self.texturehelper.gloss_mtex.texture)

        if b_mat.niftools_shader.bs_shadertype == 'BSEffectShaderProperty':
            bsshader.source_texture = TextureWriter.export_texture_filename(self.texturehelper.base_mtex.texture)
            bsshader.greyscale_texture = TextureWriter.export_texture_filename(self.texturehelper.glow_mtex.texture)

        return bsshader

    @staticmethod
    def export_shader_flags(b_mat, shader):
        b_flag_list = b_mat.niftools_shader.bl_rna.properties.keys()
        if hasattr(shader, 'shader_flags'):
            for sf_flag in shader.shader_flags._names:
                if sf_flag in b_flag_list:
                    b_flag = b_mat.niftools_shader.get(sf_flag)
                    if b_flag:
                        sf_flag_index = shader.shader_flags._names.index(sf_flag)
                        shader.shader_flags._items[sf_flag_index]._value = 1

        if hasattr(shader, 'shader_flags_1'):
            for sf_flag in shader.shader_flags_1._names:
                if sf_flag in b_flag_list:
                    b_flag = b_mat.niftools_shader.get(sf_flag)
                    if b_flag:
                        sf_flag_index = shader.shader_flags_1._names.index(sf_flag)
                        shader.shader_flags_1._items[sf_flag_index]._value = 1

        if hasattr(shader, 'shader_flags_2'):
            for sf_flag in shader.shader_flags_2._names:
                if sf_flag in b_flag_list:
                    b_flag = b_mat.niftools_shader.get(sf_flag)
                    if b_flag:
                        sf_flag_index = shader.shader_flags_2._names.index(sf_flag)
                        shader.shader_flags_2._items[sf_flag_index]._value = 1

        return shader

    def export_uv_offset(self, shader):
        shader.uv_offset.u = self.texturehelper.base_mtex.offset.x
        shader.uv_offset.v = self.texturehelper.base_mtex.offset.y

        return shader

    def export_uv_scale(self, shader):
        shader.uv_scale.u = self.texturehelper.base_mtex.scale.x
        shader.uv_scale.v = self.texturehelper.base_mtex.scale.y

        return shader

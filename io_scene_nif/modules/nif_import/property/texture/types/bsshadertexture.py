"""This script contains helper methods to import textures."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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


class BSShaderTexture:

    def import_bsshaderproperty_textures(self, b_mat, bs_shader_property):
        image_tex_file = bs_shader_property.texture_set.textures[0].decode()
        if image_tex_file:
            self.has_diffusetex = True
            self.diffuse_map = self.import_image_texture(b_mat, image_tex_file)

        image_tex_file = bs_shader_property.texture_set.textures[1].decode()
        if image_tex_file:
            self.has_normaltex = True
            self.normal_map = self.import_image_texture(b_mat, image_tex_file)

        image_tex_file = bs_shader_property.texture_set.textures[2].decode()
        if image_tex_file:
            self.has_glowtex = True
            self.glow_map = self.import_image_texture(b_mat, image_tex_file)

        image_tex_file = bs_shader_property.texture_set.textures[3].decode()
        if image_tex_file:
            self.has_detailtex = True
            self.detail_map = self.import_image_texture(b_mat, image_tex_file)

        if len(bs_shader_property.texture_set.textures) > 6:
            image_tex_file = bs_shader_property.texture_set.textures[6].decode()
            if image_tex_file:
                self.has_decaltex = True
                self.decal_map = self.import_image_texture(b_mat, image_tex_file)

            image_tex_file = bs_shader_property.texture_set.textures[7].decode()
            if image_tex_file:
                self.has_glosstex = True
                self.gloss_map = self.import_image_texture(b_mat, image_tex_file)

        if hasattr(bs_shader_property, 'texture_clamp_mode'):
            self.import_clamp(b_mat, bs_shader_property)

        if hasattr(bs_shader_property, 'uv_offset'):
            self.import_uv_offset(b_mat, bs_shader_property)

        if hasattr(bs_shader_property, 'uv_scale'):
            self.import_uv_scale(b_mat, bs_shader_property)

    def import_bseffectshaderproperty_textures(self, b_mat, bs_effect_shader_property):
        self.reset_textures()

        ImageTexFile = bs_effect_shader_property.source_texture.decode()
        if ImageTexFile:
            self.has_diffusetex = True
            self.diffuse_map = self.import_image_texture(b_mat, ImageTexFile)

        ImageTexFile = bs_effect_shader_property.greyscale_texture.decode()
        if ImageTexFile:
            self.has_glowtex = True
            self.glow_map = self.import_image_texture(b_mat, ImageTexFile)

        if hasattr(bs_effect_shader_property, 'uv_offset'):
            self.import_uv_offset(b_mat, bs_effect_shader_property)

        if hasattr(bs_effect_shader_property, 'uv_scale'):
            self.import_uv_scale(b_mat, bs_effect_shader_property)

        self.import_texture_game_properties(b_mat, bs_effect_shader_property)

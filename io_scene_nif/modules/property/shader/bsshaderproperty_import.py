"""This script contains helper methods to custom shader."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2018, NIF File Format Library and Tools contributors.
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


class BSShaderProperty:

    def __init__(self, b_mat_texslot, bs_shader_prop):
        self.b_mat_texslot = b_mat_texslot
        self.bs_shader_prop = bs_shader_prop

    def import_bsshaderproperty(self):

        # diffuse
        texture = self.bs_shader_prop.texture_set.textures[0].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        # normal
        texture = self.bs_shader_prop.texture_set.textures[1].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        # glow
        texture = self.bs_shader_prop.texture_set.textures[2].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        # detail
        texture = self.bs_shader_prop.texture_set.textures[3].decode()
        if texture:
            self.import_image_texture(self.b_mat_texslot, texture)

        if len(self.bs_shader_prop.texture_set.textures) > 6:
            # decal
            texture = self.bs_shader_prop.texture_set.textures[6].decode()
            if texture:
                self.import_image_texture(self.b_mat_texslot, texture)

            # gloss
            texture = self.bs_shader_prop.texture_set.textures[7].decode()
            if texture:
                self.import_image_texture(self.b_mat_texslot, texture)

        if hasattr(self.bs_shader_prop, 'texture_clamp_mode'):
            self.b_mat_texslot = self.import_clamp(self.b_mat_texslot, self.bs_shader_prop)
        if hasattr(self.bs_shader_prop, 'uv_offset'):
            self.b_mat_texslot = self.import_uv_offset(self.b_mat_texslot, self.bs_shader_prop)
        if hasattr(self.bs_shader_prop, 'uv_scale'):
            self.b_mat_texslot = self.import_uv_scale(self.b_mat_texslot, self.bs_shader_prop)

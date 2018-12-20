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


class BSEffectShaderProperty:

    def __init__(self, b_mat):
        self.b_mat = b_mat

    def import_bseffectshaderproperty(self, bsEffectShaderProperty):

        # diffuse
        texture = bsEffectShaderProperty.source_texture.decode()
        if texture:
            self.import_image_texture(self.b_mat, texture)

        # glow
        texture = bsEffectShaderProperty.greyscale_texture.decode()
        if texture:
            self.import_image_texture(self.b_mat, texture)

        if hasattr(bsEffectShaderProperty, 'uv_offset'):
            self.b_mat = self.import_uv_offset(self.b_mat, bsEffectShaderProperty)

        if hasattr(bsEffectShaderProperty, 'uv_scale'):
            self.b_mat = self.import_uv_scale(self.b_mat, bsEffectShaderProperty)

        self.b_mat = self.import_texture_game_properties(self.b_mat, bsEffectShaderProperty)

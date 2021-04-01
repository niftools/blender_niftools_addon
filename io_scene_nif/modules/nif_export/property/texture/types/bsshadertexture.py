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


class BSShaderTexture(TextureSlotManager):

    __instance = None

    @staticmethod
    def get():
        """ Static access method. """
        if BSShaderTexture.__instance is None:
            BSShaderTexture()
        return BSShaderTexture.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if BSShaderTexture.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            super().__init__()
            BSShaderTexture.__instance = self

    def export_bs_effect_shader_prop_textures(self, bsshader):
        bsshader.texture_set = self._create_textureset()

        if self.slots["Base"]:
            bsshader.source_texture = TextureWriter.export_texture_filename(self.slots["Base"])
        if self.slots["Glow"]:
            bsshader.greyscale_texture = TextureWriter.export_texture_filename(self.slots["Glow"])

        # clamp Mode
        bsshader.texture_clamp_mode = 65283

    def export_bs_lighting_shader_prop_textures(self, bsshader):
        texset = self._create_textureset()
        bsshader.texture_set = texset

        # Add in extra texture slots
        texset.num_textures = 9
        texset.textures.update_size()

        if self.slots["Detail"]:
            texset.textures[6] = TextureWriter.export_texture_filename(self.slots["Detail"])

        if self.slots["Gloss"]:
            texset.textures[7] = TextureWriter.export_texture_filename(self.slots["Gloss"])

        #get the offset, scale and UV wrapping mode and set them
        x_scale, y_scale, x_offset, y_offset, clamp_x, clamp_y = self.get_global_uv_transform_clip(self.slots["Base"])
        #default values for if they haven't been defined:
        if x_scale is None: x_scale = 1
        if y_scale is None: y_scale = 1
        if x_offset is None: x_offset = 0
        if y_offset is None:
            y_offset = 0
        else:
        #need to translate blender offset to nif offset to get the same results
            y_offset = 1 - y_scale - y_offset
        if clamp_x is None: clamp_x = False
        if clamp_y is None: clamp_y = False

        if hasattr(bsshader, "uv_scale"):
            bsshader.uv_scale.u = x_scale
            bsshader.uv_scale.v = y_scale

        if hasattr(bsshader, 'uv_offset'):
            bsshader.uv_offset.u = x_offset
            bsshader.uv_offset.v = y_offset

        # Texture Clamping mode
        b_img = self.slots["Base"].image
        if self.slots["Base"].extension == "CLIP":
            #if the extension is clip, we know the wrap mode is clamp for both,
            bsshader.texture_clamp_mode = NifFormat.TexClampMode.CLAMP_S_CLAMP_T
        else:
            #otherwise, look at the given clip modes from the nodes
            if not clamp_x:
                wrap_s = 2
            else:
                wrap_s = 0
            if not clamp_y:
                wrap_t = 1
            else:
                wrap_t = 0
            bsshader.texture_clamp_mode = (wrap_s + wrap_t)

    def export_bs_shader_pp_lighting_prop_textures(self, bsshader):
        bsshader.texture_set = self._create_textureset()

    def _create_textureset(self):
        texset = NifFormat.BSShaderTextureSet()

        if self.slots["Base"]:
            texset.textures[0] = TextureWriter.export_texture_filename(self.slots["Base"])

        if self.slots["Normal"]:
            texset.textures[1] = TextureWriter.export_texture_filename(self.slots["Normal"])

        if self.slots["Glow"]:
            texset.textures[2] = TextureWriter.export_texture_filename(self.slots["Glow"])

        if self.slots["Detail"]:
            texset.textures[3] = TextureWriter.export_texture_filename(self.slots["Detail"])

        return texset

    def export_uv_offset(self, shader):
        shader.uv_offset.u = self.slots["Base"].offset.x
        shader.uv_offset.v = self.slots["Base"].offset.y

        return shader

    def export_uv_scale(self, shader):
        shader.uv_scale.u = self.slots["Base"].scale.x
        shader.uv_scale.v = self.slots["Base"].scale.y

        return shader

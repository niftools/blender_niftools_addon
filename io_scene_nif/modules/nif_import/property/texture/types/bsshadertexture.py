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
from io_scene_nif.modules.nif_import.property.texture import TextureSlotManager
from io_scene_nif.utils.util_logging import NifLog


class BSShaderTexture(TextureSlotManager):

    __instance = None

    def __init__(self):
        """ Virtually private constructor. """
        if BSShaderTexture.__instance:
            raise Exception("This class is a singleton!")
        else:
            super().__init__()
            BSShaderTexture.__instance = self

    @staticmethod
    def get():
        """ Static access method. """
        if not BSShaderTexture.__instance:
            BSShaderTexture()
        return BSShaderTexture.__instance

    def import_bsshaderproperty_textureset(self, b_mat, bs_shader_property):
        texture_set = bs_shader_property.texture_set
        textures = texture_set.textures

        self._load_diffuse(b_mat, textures[0])

        normal_map = textures[1].decode()
        if normal_map:
            NifLog.debug("Loading normal map {0}".format(normal_map))
            b_texture = self.create_texture_slot(b_mat, normal_map)
            self.update_normal_slot(b_texture)

        self._load_glow(b_mat, textures[2])

        detail_map = textures[3].decode()
        if detail_map:
            NifLog.debug("Loading detail texture {0}".format(detail_map))
            b_texture = self.create_texture_slot(b_mat, detail_map)
            self.update_detail_slot(b_texture)

        if len(textures) > 6:
            decal_map = textures[6].decode()
            if decal_map:
                NifLog.debug("Loading decal texture {0}".format(decal_map))
                b_texture = self.create_texture_slot(b_mat, decal_map)
                self.update_decal_slot(b_texture)

            gloss_map = textures[7].decode()
            if gloss_map:
                NifLog.debug("Loading gloss map {0}".format(gloss_map))
                b_texture = self.create_texture_slot(b_mat, gloss_map)
                self.update_gloss_slot(b_texture)

    def import_bseffectshaderproperty_textures(self, b_mat, bs_effect_shader_property):

        self._load_diffuse(b_mat, bs_effect_shader_property.source_texture)

        self._load_glow(b_mat, bs_effect_shader_property.source_texture)

        # self.import_texture_game_properties(b_mat, bs_effect_shader_property)

    def _load_diffuse(self, b_mat, texture):
        diffuse_map = texture.decode()
        if diffuse_map:
            NifLog.debug("Loading diffuse texture {0}".format(diffuse_map))
            b_texture = self.create_texture_slot(b_mat, diffuse_map)
            self.link_diffuse_node(b_texture)

    def _load_glow(self, b_mat, texture):
        glow_map = texture.decode()
        if glow_map:
            NifLog.debug("Loading glow texture {0}".format(glow_map))
            b_texture = self.create_texture_slot(b_mat, glow_map)
            self.update_glow_slot(b_texture)

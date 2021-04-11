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
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.consts import TEX_SLOTS


class BSShaderTexture:

    __instance = None
    _nodes_wrapper = None

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

    def import_bsshaderproperty_textureset(self, bs_shader_property, nodes_wrapper):
        textures = bs_shader_property.texture_set.textures
        slots = {
            TEX_SLOTS.BASE: 0,
            TEX_SLOTS.NORMAL: 1,
            TEX_SLOTS.GLOW: 2,
            TEX_SLOTS.DETAIL: 3,
            TEX_SLOTS.GLOSS: 7,
            TEX_SLOTS.BUMP_MAP: None,
            TEX_SLOTS.DECAL_0: 6,
            TEX_SLOTS.DECAL_1: None,
            TEX_SLOTS.DECAL_2: None,
            # extra shader stuff?
            TEX_SLOTS.SPECULAR: None,
        }
        for slot_name, slot_i in slots.items():
            # skip those whose index we don't know from old code
            if slot_i is not None and len(textures) > slot_i:
                tex_str = textures[slot_i].decode()
                # see if it holds a texture
                if tex_str:
                    NifLog.debug(f"Shader has active {slot_name}")
                    nodes_wrapper.create_and_link(slot_name, tex_str)

    def import_bseffectshaderproperty_textures(self, bs_effect_shader_property, nodes_wrapper):

        base = bs_effect_shader_property.source_texture.decode()
        if base:
            nodes_wrapper.create_and_link(TEX_SLOTS.BASE, base)

        glow = bs_effect_shader_property.greyscale_texture.decode()
        if glow:
            nodes_wrapper.create_and_link(TEX_SLOTS.GLOW, glow)

        # self.import_texture_game_properties(b_mat, bs_effect_shader_property)

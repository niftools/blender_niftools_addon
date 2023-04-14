"""This modules contains helper methods to import nitexturepropery based texture."""

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


class NiTextureProp:

    __instance = None

    def __init__(self):
        self.slots = {}
        for slot_name in vars(TEX_SLOTS).values():
            self.slots[slot_name] = None

    def import_nitextureprop_textures(self, n_texture_desc, nodes_wrapper):
        # NifLog.debug(f"Importing {n_texture_desc}")

        all_empty = True
        # go over all valid texture slots
        for slot_name, _ in self.slots.items():
            # get the field name used by nif xml for this texture
            slot_lower = slot_name.lower().replace(' ', '_')
            field_name = f"{slot_lower}_texture"
            # get the tex desc link
            has_tex = getattr(n_texture_desc, "has_"+field_name, None)
            if has_tex:
                # NifLog.warn(f"Texdesc has active {slot_name}")
                n_tex = getattr(n_texture_desc, field_name)
                nodes_wrapper.create_and_link(slot_name, n_tex)
                all_empty = False
        if all_empty:
            NifLog.warn(
                f"Tried importing a texture, but slots are empty, so trying to reach shader_textures")
            # NifLog.warn(n_texture_desc)
            shader_textures = getattr(n_texture_desc, 'shader_textures', None)
            if shader_textures:
                if len(shader_textures) > 0:
                    texture_data = getattr(shader_textures[0], 'texture_data')
                    is_used = getattr(shader_textures[0], 'is_used')
                    if texture_data and is_used:
                        NifLog.warn('linking base slot')
                        nodes_wrapper.create_and_link(
                            TEX_SLOTS.BASE, texture_data)
                # check for map
                for texture in shader_textures:
                    texture_data = getattr(texture, 'texture_data')
                    is_used = getattr(texture, 'is_used')
                    if texture_data and is_used:
                        source = getattr(texture_data, 'source', None)
                        if source:
                            file_name = getattr(source, 'file_name', None)
                            if file_name:
                                if 'CompleteMap' in str(file_name):
                                    NifLog.warn(str(file_name))
                                    nodes_wrapper.create_and_link(
                                        TEX_SLOTS.DETAIL, texture_data)

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
        # go over all valid texture slots
        for slot_name, _ in self.slots.items():
            # get the field name used by nif xml for this texture
            slot_lower = slot_name.lower().replace(' ', '_')
            field_name = f"{slot_lower}_texture"
            # get the tex desc link
            has_tex = getattr(n_texture_desc, "has_"+field_name, None)
            if has_tex:
                NifLog.debug(f"Texdesc has active {slot_name}")
                n_tex = getattr(n_texture_desc, field_name)
                nodes_wrapper.create_and_link(slot_name, n_tex)

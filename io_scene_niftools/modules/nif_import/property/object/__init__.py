"""This script contains helper methods to import objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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
import bpy
from pyffi.formats.nif import NifFormat

from io_scene_niftools.properties.object import PRN_DICT
from math import pi


class ObjectProperty:

    # TODO [property] Add delegate processing
    def import_extra_datas(self, root_block, b_obj):
        """ Only to be called on nif and blender root objects! """
        # store type of root node
        if isinstance(root_block, NifFormat.BSFadeNode):
            b_obj.niftools.rootnode = 'BSFadeNode'
        else:
            b_obj.niftools.rootnode = 'NiNode'
        # store its flags
        b_obj.niftools.flags = root_block.flags
        # store extra datas
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.NiStringExtraData):
                # weapon location or attachment position
                if n_extra.name.decode() == "Prn":
                    game = bpy.context.scene.niftools_scene.game
                    if game in PRN_DICT[next(iter(PRN_DICT))]:
                        # first check specifically in that game
                        for slot, game_map in PRN_DICT.items():
                            if game_map[game].lower() == n_extra.string_data.decode().lower():
                                b_obj.niftools.prn_location = slot
                                break
                    if b_obj.niftools.prn_location == "NONE":
                        # we didn't find anything, either because the game doesn't have it,
                        # or we have the wrong game. Check all key, value pairs
                        for slot, game_map in PRN_DICT.items():
                            for k, v in game_map:
                                if v.lower() == n_extra.string_data.decode().lower():
                                    b_obj.niftools.prn_location = slot
                                    break
                            else:
                                continue
                            break
                elif n_extra.name.decode() == "UPB":
                    b_obj.niftools.upb = n_extra.string_data.decode()
            elif isinstance(n_extra, NifFormat.BSXFlags):
                b_obj.niftools.bsxflags = n_extra.integer_data
            elif isinstance(n_extra, NifFormat.BSInvMarker):
                b_obj.niftools_bs_invmarker.add()
                b_obj.niftools_bs_invmarker[0].name = n_extra.name.decode()
                b_obj.niftools_bs_invmarker[0].bs_inv_x = (-n_extra.rotation_x / 1000) % (2 * pi)
                b_obj.niftools_bs_invmarker[0].bs_inv_y = (-n_extra.rotation_y / 1000) % (2 * pi)
                b_obj.niftools_bs_invmarker[0].bs_inv_z = (-n_extra.rotation_z / 1000) % (2 * pi)
                b_obj.niftools_bs_invmarker[0].bs_inv_zoom = n_extra.zoom

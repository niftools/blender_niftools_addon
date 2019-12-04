"""This module contains helper methods to export geometry morph data."""

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

from pyffi.formats.egm import EgmFormat

from io_scene_nif.modules.animation.morph_export import MorphAnimation
from io_scene_nif.utility.util_global import EGMData
from io_scene_nif.utility.util_logging import NifLog


class Morph:

    def __init__(self):
        EGMData.data = None
        self.morph_animation = MorphAnimation()

    def export_egm(self, key_blocks):
        EGMData.data = EgmFormat.Data(num_vertices=len(key_blocks[0].data))
        for key_block in key_blocks:
            if key_block.name.startswith("EGM SYM"):
                morph = EGMData.data.add_sym_morph()
            elif key_block.name.startswith("EGM ASYM"):
                morph = EGMData.data.add_asym_morph()
            else:
                continue
            NifLog.info("Exporting morph {0} to egm".format(key_block.name))
            relative_vertices = []

            # note: key_blocks[0] is base key
            for vert, key_vert in zip(key_blocks[0].data, key_block.data):
                relative_vertices.append(key_vert - vert)
            morph.set_relative_vertices(relative_vertices)

    def export_morph(self, b_mesh, b_obj, tridata, trishape, vertlist, vertmap):
        # shape key morphing
        key = b_mesh.shape_keys
        if key:
            if len(key.key_blocks) > 1:
                # yes, there is a key object attached
                # export as egm, or as morph_data?
                if key.key_blocks[1].name.startswith("EGM"):
                    # egm export!
                    self.export_egm(key.key_blocks)
                elif key.ipo:
                    self.morph_animation.export_morph_animation(b_mesh, key, trishape, len(vertlist), vertmap)

                    # fix data consistency type
                    tridata.consistency_flags = b_obj.niftools.consistency_flags

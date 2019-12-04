"""This script contains classes to help import animations."""

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

from io_scene_nif.utility.util_global import EGMData


class Morph:

    def import_egm_morphs(self, b_obj, v_map, n_verts):
        """Import all EGM morphs as shape keys for blender object."""
        # TODO [morph][egm] if there is an egm, the assumption is that there is only one mesh in the nif
        b_mesh = b_obj.data
        sym_morphs = [list(morph.get_relative_vertices()) for morph in EGMData.data.sym_morphs]
        asym_morphs = [list(morph.get_relative_vertices()) for morph in EGMData.data.asym_morphs]

        # insert base key at frame 1, using absolute keys
        sk_basis = b_obj.shape_key_add("Basis")
        b_mesh.shape_keys.use_relative = False

        morphs = ([(morph, "EGM SYM %i" % i) for i, morph in enumerate(sym_morphs)] +
                  [(morph, "EGM ASYM %i" % i) for i, morph in enumerate(asym_morphs)])

        for morph_verts, key_name in morphs:
            # convert tuples into vector here so we can simply add in morph_mesh()
            morphvert_out = []
            for u in morph_verts:
                v = NifFormat.Vector3()
                v.x, v.y, v.z = u
                morphvert_out.append(v)
            self.morph_mesh(b_mesh, n_verts, morphvert_out, v_map)
            # TODO [animation] unused variable is it required
            shape_key = b_obj.shape_key_add(key_name, from_mix=False)

    def morph_mesh(self, b_mesh, baseverts, morphverts, v_map):
        """Transform a mesh to be in the shape given by morphverts."""
        # for each vertex calculate the key position from base
        # pos + delta offset
        # length check disabled
        # as sometimes, oddly, the morph has more vertices...
        # assert(len(baseverts) == len(morphverts) == len(v_map))
        for bv, mv, b_v_index in zip(baseverts, morphverts, v_map):
            # pyffi vector3
            v = bv + mv
            # if applytransform:
            # v *= transform
            b_mesh.vertices[b_v_index].co = v.as_tuple()

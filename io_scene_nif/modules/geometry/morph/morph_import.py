"""This module contains helper methods to import morph data."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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

import mathutils

from io_scene_nif.utility.nif_global import NifData, NifOp


class GeoMorph:

    def import_geomoraph(self, b_mesh, n_verts, v_map, applytransform, transform):

        # import facegen morphs
        if NifData.EGMDATA:

            egmdata = NifData.EGMDATA
            # XXX if there is an egm, the assumption is that there is only one
            # XXX mesh in the nif
            sym_morphs = [list(morph.get_relative_vertices()) for morph in egmdata.sym_morphs]
            asym_morphs = [list(morph.get_relative_vertices()) for morph in egmdata.asym_morphs]

            # insert base key at frame 1, using relative keys
            b_mesh.insertKey(1, 'relative')

            if NifOp.props.IMPORT_EGMANIM:
                # if morphs are animated: create key ipo for mesh
                b_ipo = Blender.Ipo.New('Key', 'KeyIpo')
                b_mesh.key.ipo = b_ipo

            morphs = ([(morph, "EGM SYM %i" % i) for i, morph in enumerate(sym_morphs)] +
                      [(morph, "EGM ASYM %i" % i) for i, morph in enumerate(asym_morphs)])

            for morphverts, keyname in morphs:
                # length check disabled
                # as sometimes, oddly, the morph has more vertices...
                # assert(len(verts) == len(morphverts) == len(v_map))

                # for each vertex calculate the key position from base
                # pos + delta offset
                for bv, mv, b_v_index in zip(n_verts, morphverts, v_map):
                    base = mathutils.Vector(bv.x, bv.y, bv.z)
                    delta = mathutils.Vector(mv[0], mv[1], mv[2])
                    v = base + delta
                    if applytransform:
                        v *= transform
                    b_mesh.vertices[b_v_index].co[0] = v.x
                    b_mesh.vertices[b_v_index].co[1] = v.y
                    b_mesh.vertices[b_v_index].co[2] = v.z
                # update the mesh and insert key
                b_mesh.insertKey(1, 'relative')
                # set name for key
                b_mesh.key.blocks[-1].name = keyname

                if self.IMPORT_EGMANIM:
                    # set up the ipo key curve
                    b_curve = b_ipo.addCurve(keyname)
                    # linear interpolation
                    b_curve.interpolation = Blender.IpoCurve.InterpTypes.LINEAR
                    # constant extrapolation
                    b_curve.extend = Blender.IpoCurve.ExtendTypes.CONST
                    # set up the curve's control points
                    framestart = 1 + len(b_mesh.key.blocks) * 10
                    for frame, value in ((framestart, 0),
                                         (framestart + 5, self.IMPORT_EGMANIMSCALE),
                                         (framestart + 10, 0)):
                        b_curve.addBezier((frame, value))

            if self.IMPORT_EGMANIM:
                # set begin and end frame
                bpy.context.scene.getRenderingContext().startFrame(1)
                bpy.context.scene.getRenderingContext().endFrame(
                    11 + len(b_mesh.key.blocks) * 10)

            # finally: return to base position
            for bv, b_v_index in zip(n_verts, v_map):
                base = mathutils.Vector(bv.x, bv.y, bv.z)
                if applytransform:
                    base *= transform
                b_mesh.vertices[b_v_index].co[0] = base.x
                b_mesh.vertices[b_v_index].co[1] = base.y
                b_mesh.vertices[b_v_index].co[2] = base.z
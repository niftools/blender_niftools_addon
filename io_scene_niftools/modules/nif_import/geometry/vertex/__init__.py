"""This script contains helper methods to import vertex data."""

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

from io_scene_niftools.utils.singleton import NifOp


class Vertex:

    @staticmethod
    def map_vertex_colors(b_mesh, n_tri_data):
        if n_tri_data.has_vertex_colors:
            b_mesh.vertex_colors.new(name=f"RGBA")
            b_mesh.vertex_colors[-1].data.foreach_set("color", [channel for col in [n_tri_data.vertex_colors[loop.vertex_index] for loop in b_mesh.loops] for channel in (col.r, col.g, col.b, col.a)])

    @staticmethod
    def map_uv_layer(b_mesh, n_tri_data):
        """ UV coordinates, NIF files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seam.
            So whenever a hard edge or a UV seam is present the mesh, vertices are duplicated.
            Blender only must duplicate vertices for hard edges; duplicating for UV seams would introduce unnecessary hard edges."""

        # "sticky" UV coordinates: these are transformed in Blender UV's
        for uv_i, uv_set in enumerate(n_tri_data.uv_sets):
            b_mesh.uv_layers.new(name=f"UV{uv_i}")
            b_mesh.uv_layers[-1].data.foreach_set("uv", [coord for uv in [uv_set[loop.vertex_index] for loop in b_mesh.loops] for coord in (uv.u, 1.0 - uv.v)])

    @staticmethod
    def map_normals(b_mesh, n_tri_data):
        """Import nif normals as custom normals."""
        if not n_tri_data.has_normals:
            return
        assert len(b_mesh.vertices) == len(n_tri_data.normals)
        # set normals
        if NifOp.props.use_custom_normals:
            # map normals so we can set them to the edge corners (stored per loop)
            no_array = []
            for face in b_mesh.polygons:
                for vertex_index in face.vertices:
                    # no_array.append(model.normals[vertex_index])
                    # no_array.append(mathutils.Vector(n_tri_data.normals[vertex_index]).normalized())
                    no_array.append(n_tri_data.normals[vertex_index].as_tuple())
                    # no_array.append((0,0,1))
                # no_array.append(model.tangents[vertex_index])
                # face.use_smooth = True

            b_mesh.use_auto_smooth = True
            b_mesh.normals_split_custom_set(no_array)

    @staticmethod
    def get_uv_layer_name(uvset):
        return "UV{:d}".format(uvset)

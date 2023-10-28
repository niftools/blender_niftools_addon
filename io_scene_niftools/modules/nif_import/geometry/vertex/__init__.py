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

import numpy as np

from io_scene_niftools.utils.singleton import NifOp


class Vertex:

    @staticmethod
    def map_vertex_colors(b_mesh, vertex_colors):
        # [TODO] in Blender 3.2, vertex_colors was deprecated (https://wiki.blender.org/wiki/Reference/Release_Notes/3.2/Python_API)
        # so use Color attribute instead when 3.2 or greater
        b_mesh.vertex_colors.new(name=f"RGBA")
        b_mesh.vertex_colors[-1].data.foreach_set("color", [channel for col in [vertex_colors[loop.vertex_index] for loop in b_mesh.loops] for channel in (col.r, col.g, col.b, col.a)])

    @staticmethod
    def map_uv_layer(b_mesh, uv_sets):
        """ UV coordinates, NIF files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seam.
            So whenever a hard edge or a UV seam is present the mesh, vertices are duplicated.
            Blender only must duplicate vertices for hard edges; duplicating for UV seams would introduce unnecessary hard edges."""

        # "sticky" UV coordinates: these are transformed in Blender UV's
        for uv_i, uv_set in enumerate(uv_sets):
            b_mesh.uv_layers.new(name=f"UV{uv_i}")
            b_mesh.uv_layers[-1].data.foreach_set("uv", [coord for uv in [uv_set[loop.vertex_index] for loop in b_mesh.loops] for coord in (uv.u, 1.0 - uv.v)])

    @staticmethod
    def map_normals(b_mesh, normals):
        """Import nif normals as custom normals."""
        assert len(b_mesh.vertices) == len(normals)
        # set normals
        if NifOp.props.use_custom_normals:
            no_array = np.array(normals)
            # the normals need to be pre-normalized or blender will do it inconsistely, leading to marked sharp edges
            no_array = Vertex.normalize(no_array)
            # use normals_split_custom_set_from_vertices to set the loop custom normals from the per-vertex normals
            b_mesh.use_auto_smooth = True
            b_mesh.normals_split_custom_set_from_vertices(no_array)

    @staticmethod
    def normalize(vector_array):
        vector_norms = np.linalg.norm(vector_array, ord=2, axis=1, keepdims=True)
        non_zero_norms = np.reshape(vector_norms != 0, newshape = len(vector_array))
        normalized_vectors = np.copy(vector_array)
        normalized_vectors[non_zero_norms] /= vector_norms[non_zero_norms]
        return normalized_vectors

    @staticmethod
    def get_uv_layer_name(uvset):
        return "UV{:d}".format(uvset)

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


class Vertex:

    @staticmethod
    def map_vertex_colors(b_mesh, n_data, v_map):
        # vertex colors
        if b_mesh.polygons and n_data.vertex_colors:
            n_vcol_map = list()
            for n_vcol, n_vmap in zip(n_data.vertex_colors, v_map):
                n_vcol_map.append((n_vcol, n_vmap))

            # create vertex_layers
            if "VertexColor" not in b_mesh.vertex_colors:
                b_mesh.vertex_colors.new(name="VertexColor")  # color layer
                b_mesh.vertex_colors.new(name="VertexAlpha")  # greyscale

            # Mesh Vertex Color / Mesh Face
            for b_polygon_loop in b_mesh.loops:
                b_loop_index = b_polygon_loop.index
                vcol = b_mesh.vertex_colors["VertexColor"].data[b_loop_index]
                vcola = b_mesh.vertex_colors["VertexAlpha"].data[b_loop_index]
                for n_col_index, n_map_index in n_vcol_map:
                    if n_map_index == b_polygon_loop.vertex_index:
                        col_list = n_col_index
                        vcol.color.r = col_list.r
                        vcol.color.g = col_list.g
                        vcol.color.b = col_list.b
                        vcola.color.v = col_list.a
            # vertex colors influence lighting...
            # we have to set the use_vertex_color_light flag on the material, see below

    @staticmethod
    def map_uv_layer(b_mesh, bf2_index, n_triangles, n_uvco, n_data):
        """ UV coordinates, NIF files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seam.
            So whenever a hard edge or a UV seam is present the mesh, vertices are duplicated.
            Blender only must duplicate vertices for hard edges; duplicating for UV seams would introduce unnecessary hard edges."""

        # only import UV if there are polygons (some corner cases have only one vertex, and no polygons, and b_mesh.faceUV = 1 on such mesh raises a runtime error)
        if b_mesh.polygons:
            for n_uv_set in range(len(n_data.uv_sets)):
                # Set the face UV's for the mesh. The NIF format only supports vertex UV's.
                # However Blender only allows explicit editing of face  UV's, so load vertex UV's as face UV's
                uv_layer = str(n_uv_set)
                if uv_layer not in b_mesh.uv_textures:
                    b_mesh.uv_textures.new(uv_layer)

                b_uv_layer = b_mesh.uv_layers[uv_layer].data[:]
                for b_f_index, f in enumerate(n_triangles):
                    if b_f_index is None:
                        continue
                    v1, v2, v3 = f
                    b_poly_index = b_mesh.polygons[b_f_index + bf2_index]
                    b_uv_layer[b_poly_index.loop_start].uv = n_uvco[n_uv_set][v1]
                    b_uv_layer[b_poly_index.loop_start + 1].uv = n_uvco[n_uv_set][v2]
                    b_uv_layer[b_poly_index.loop_start + 2].uv = n_uvco[n_uv_set][v3]
            b_mesh.uv_textures.active_index = 0

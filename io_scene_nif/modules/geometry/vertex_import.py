"""This script contains helper methods to import vertex data."""

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
from io_scene_nif.modules.property.texture.texture_import import TextureSlots


class Vertex:

    def process_vertex_colors(self, b_mesh, niData, v_map):
        # vertex colors
        if b_mesh.polygons and niData.vertex_colors:
            n_vcol_map = list()
            for n_vcol, n_vmap in zip(niData.vertex_colors, v_map):
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
            # we have to set the use_vertex_color_light flag on the material

    @staticmethod
    def process_uv_coordinates(b_mesh, bf2_index, n_uvco, nidata, poly_gens):
        """Import UV coordinates
        NIF files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seam.
        So whenever a hard edge or a UV seam is present the mesh, vertices are duplicated.
        Blender only must duplicate vertices for hard edges; duplicating for UV seams would introduce unnecessary hard edges.
        only import UV if there are polygons (some corner cases have only one vertex, and no polygons,and b_mesh.faceUV = 1 on such mesh raises a runtime error)"""

        for i in range(len(nidata.uv_sets)):
            # Set the face UV's for the mesh.
            # The NIF format only supports vertex UV's, but Blender only allows explicit editing of face UV's, so load vertex UV's as face UV's
            uv_layer = Vertex.get_uv_layer_name(i)
            if uv_layer not in b_mesh.uv_textures:
                b_mesh.uv_textures.new(uv_layer)
                uv_faces = b_mesh.uv_textures.active.data[:]
            elif uv_layer in b_mesh.uv_textures:
                uv_faces = b_mesh.uv_textures[uv_layer].data[:]
            else:
                uv_faces = None
            if uv_faces:
                uvl = b_mesh.uv_layers.active.data[:]
                for b_f_index, f in enumerate(poly_gens):
                    if b_f_index is None:
                        continue
                    uvlist = f
                    v1, v2, v3 = uvlist
                    # if v3 == 0:
                    #   v1,v2,v3 = v3,v1,v2
                    b_poly_index = b_mesh.polygons[b_f_index + bf2_index]
                    uvl[b_poly_index.loop_start].uv = n_uvco[v1]
                    uvl[b_poly_index.loop_start + 1].uv = n_uvco[v2]
                    uvl[b_poly_index.loop_start + 2].uv = n_uvco[v3]
        b_mesh.uv_textures.active_index = 0

    @staticmethod
    def get_uv_layer_name(uvset):
        return "UVMap.%03i" % uvset if uvset != 0 else "UVMap"

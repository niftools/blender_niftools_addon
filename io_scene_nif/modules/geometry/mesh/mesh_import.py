"""This module contains helper methods to import Mesh information."""
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


from io_scene_nif.utility.util_logging import NifLog


class Mesh:

    @staticmethod
    def add_triangles_to_bmesh(b_mesh, n_triangles, v_map):
        # Indices for later
        b_poly_index = len(b_mesh.polygons)  # TODO [general] Replace with add to end
        b_poly_offset = len(b_mesh.polygons)
        b_loop_index = len(b_mesh.loops)

        # add polys to mesh
        num_trianges = len(n_triangles)
        poly_count = num_trianges
        b_mesh.polygons.add(poly_count)
        b_mesh.loops.add(poly_count * 3)

        f_map = [None] * num_trianges
        unique_faces = list()  # to avoid duplicate polygons
        tri_point_list = list()
        for n_tri_index, n_triangle in enumerate(n_triangles):
            # get face index
            f_verts = [v_map[n_vert] for n_vert in n_triangle]
            if tuple(f_verts) in unique_faces:
                continue

            unique_faces.append(tuple(f_verts))
            f_map[n_tri_index] = b_poly_index
            tri_point_list.append(len(n_triangles[n_tri_index]))
            b_poly_index += 1

        ls_list = list()
        num_unique_faces = len(unique_faces)
        for ls1 in range(0, num_unique_faces * (tri_point_list[len(ls_list)]), (tri_point_list[len(ls_list)])):
            ls_list.append((ls1 + b_loop_index))

        for n_tri_index in range(num_unique_faces):
            face_index = f_map[n_tri_index]
            if face_index is None:
                continue
            b_mesh.polygons[face_index].loop_start = ls_list[(face_index - b_poly_offset)]
            b_mesh.polygons[face_index].loop_total = len(unique_faces[(face_index - b_poly_offset)])

            loop = 0
            lp_points = [v_map[loop_point] for loop_point in n_triangles[(face_index - b_poly_offset)]]
            num_loops = len(n_triangles[(face_index - b_poly_offset)])
            while loop < num_loops:
                b_mesh.loops[(loop + b_loop_index)].vertex_index = lp_points[loop]
                loop += 1

            b_loop_index += num_loops
        # at this point, deleted polygons (degenerate or duplicate) satisfy f_map[i] = None
        NifLog.debug("{0} unique polygons".format(num_unique_faces))
        return b_poly_offset, f_map
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

import mathutils

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.nif_import.animation.morph import MorphAnimation
from io_scene_nif.modules.nif_import.geometry.vertex.groups import VertexGroup
from io_scene_nif.modules.nif_import.geometry import mesh
from io_scene_nif.modules.nif_import.geometry.vertex import Vertex
from io_scene_nif.modules.nif_import.property.material import Material
from io_scene_nif.modules.nif_import.property.geometry.mesh import MeshPropertyProcessor
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_global import NifOp, EGMData
from io_scene_nif.utils.util_logging import NifLog

# TODO [scene][property][ui] Expose these either through the scene or as ui properties
VERTEX_RESOLUTION = 1000
NORMAL_RESOLUTION = 100


class Mesh:

    def __init__(self):
        self.materialhelper = Material()
        self.morph_anim = MorphAnimation()
        self.mesh_prop_processor = MeshPropertyProcessor()

    def import_mesh(self, n_block, b_obj, transform=None):
        """Creates and returns a raw mesh, or appends geometry data to group_mesh.

        :param n_block: The nif block whose mesh data to import.
        :type n_block: C{NiTriBasedGeom}
        :param b_obj: The mesh to which to append the geometry data. If C{None}, a new mesh is created.
        :type b_obj: A Blender object that has mesh data.
        :param transform: Apply the n_block's transformation to the mesh.
        :type transform: C{Matix}
        """
        assert (isinstance(n_block, NifFormat.NiTriBasedGeom))

        node_name = n_block.name.decode()
        NifLog.info("Importing mesh data for geometry '{0}'".format(node_name))
        b_mesh = b_obj.data

        # shortcut for mesh geometry data
        n_tri_data = n_block.data
        if not n_tri_data:
            raise util_math.NifError("No shape data in {0}".format(node_name))

        # polygons
        n_triangles = [list(tri) for tri in n_tri_data.get_triangles()]

        # "sticky" UV coordinates: these are transformed in Blender UV's
        n_uvco = tuple(tuple((lw.u, 1.0 - lw.v) for lw in uv_set) for uv_set in n_tri_data.uv_sets)

        # TODO [properties] Should this be object level process, secondary pass for materials / caching
        self.mesh_prop_processor.process_property_list(n_block, b_obj.data)

        v_map = Mesh.map_n_verts_to_b_verts(b_mesh, n_tri_data, transform)

        bf2_index, f_map = Mesh.add_triangles_to_bmesh(b_mesh, n_triangles, v_map)

        is_smooth = True if (n_tri_data.has_normals or n_block.skin_instance) else False
        self.set_face_smooth(b_mesh, f_map, is_smooth)

        Vertex.map_vertex_colors(b_mesh, n_tri_data, v_map)

        Vertex.map_uv_layer(b_mesh, bf2_index, n_triangles, n_uvco, n_tri_data)

        # FIXME [material][texture] This should be reimplemented
        # self.materialhelper.set_material_vertex_mapping(b_mesh, f_map, n_uvco)

        # import skinning info, for meshes affected by bones
        VertexGroup.import_skin(n_block, b_obj, v_map)

        # import morph controller
        if NifOp.props.animation:
            self.morph_anim.import_morph_controller(n_block, b_obj, v_map)
        # import facegen morphs
        if EGMData.data:
            self.morph_anim.import_egm_morphs(b_obj, v_map, n_tri_data)

        # recalculate mesh to render correctly
        # implementation note: update() without validate() can cause crash

        b_mesh.validate()
        b_mesh.update()

    @staticmethod
    def set_face_smooth(b_mesh, f_map, smooth):
        """set face smoothing and material"""

        for b_poly_index in f_map:
            if b_poly_index is None:
                continue
            poly = b_mesh.polygons[b_poly_index]
            poly.use_smooth = smooth
            poly.material_index = 0  # only one material

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

    @staticmethod
    def map_n_verts_to_b_verts(b_mesh, n_tri_data, transform):
        # vertices
        n_verts = n_tri_data.vertices

        # vertex normals
        n_norms = n_tri_data.normals

        # v_map will store the vertex index mapping
        # nif vertex i maps to blender vertex v_map[i]
        v_map = [_ for _ in range(len(n_verts))]  # pre-allocate memory, for faster performance
        # Following code avoids introducing unwanted cracks in UV seams:
        # Construct vertex map to get unique vertex / normal pair list.
        # We use a Python dictionary to remove doubles and to keep track of indices.
        # While we are at it, we also add vertices while constructing the map.
        n_map = {}
        b_v_index = len(b_mesh.vertices)  # case we are adding to mesh with existing vertices
        for n_vert_index, n_vert in enumerate(n_verts):
            # The key k identifies unique vertex /normal pairs.
            # We use a tuple of ints for key, this works MUCH faster than a tuple of floats.
            if n_norms:
                n_norm = n_norms[n_vert_index]
                key = (int(n_vert.x * mesh.VERTEX_RESOLUTION),
                       int(n_vert.y * mesh.VERTEX_RESOLUTION),
                       int(n_vert.z * mesh.VERTEX_RESOLUTION),
                       int(n_norm.x * mesh.NORMAL_RESOLUTION),
                       int(n_norm.y * mesh.NORMAL_RESOLUTION),
                       int(n_norm.z * mesh.NORMAL_RESOLUTION))
            else:
                key = (int(n_vert.x * mesh.VERTEX_RESOLUTION),
                       int(n_vert.y * mesh.VERTEX_RESOLUTION),
                       int(n_vert.z * mesh.VERTEX_RESOLUTION))

            # check if vertex was already added, and if so, what index
            try:
                # this is the bottle neck...
                # can we speed this up?
                if not NifOp.props.combine_vertices:
                    n_map_k = None
                else:
                    n_map_k = n_map[key]
            except KeyError:
                n_map_k = None

            if not n_map_k:
                # no entry: new vertex / normal pair
                n_map[key] = n_vert_index  # unique vertex / normal pair with key k was added, with NIF index i
                v_map[n_vert_index] = b_v_index  # NIF vertex i maps to blender vertex b_v_index
                if transform:
                    n_vert = mathutils.Vector([n_vert.x, n_vert.y, n_vert.z])
                    n_vert = transform * n_vert

                # add the vertex
                b_mesh.vertices.add(1)
                b_mesh.vertices[-1].co = [n_vert.x, n_vert.y, n_vert.z]
                # adds normal info if present (Blender recalculates these when switching between edit mode and object mode, handled further)
                # if n_norms:
                #    mv = b_mesh.vertices[b_v_index]
                #    n = n_norms[i]
                #    mv.normal = mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                # NIF vertex i maps to Blender vertex v_map[n_map_k]
                v_map[n_vert_index] = v_map[n_map_k]
        # report
        NifLog.debug("{0} unique vertex-normal pairs".format(str(len(n_map))))
        # release memory
        del n_map
        return v_map

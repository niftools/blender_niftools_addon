"""This script contains helper methods to import geometry data."""

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

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature, geometry
from io_scene_nif.modules.animation.animation_import import GeometryAnimation
from io_scene_nif.modules.geometry.skin.skin_import import Skin
from io_scene_nif.modules.geometry.mesh.vertex_import import Vertex
from io_scene_nif.modules.obj import object_import
from io_scene_nif.modules.property.property_import import Property
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


class Mesh:

    @staticmethod
    def import_mesh(n_block, group_mesh=None, applytransform=False, relative_to=None):
        """Creates and returns a raw mesh, or appends geometry data to group_mesh.

        :param relative_to:
        :param n_block: The nif block whose mesh data to import.
        :type n_block: C{NiTriBasedGeom}
        :param group_mesh: The mesh to which to append the geometry
            data. If C{None}, a new mesh is created.
        :type group_mesh: A Blender object that has mesh data.
        :param applytransform: Whether to apply the niBlock's
            transformation to the mesh. If group_mesh is not C{None},
            then applytransform must be C{True}.
        :type applytransform: C{bool}
        """
        assert (isinstance(n_block, NifFormat.NiTriBasedGeom))

        NifLog.info("Importing mesh data for geometry {0}".format(n_block.name))

        if group_mesh:
            b_obj = group_mesh
            b_mesh = group_mesh.data
        else:
            # Mesh name -> must be unique, so tag it if needed
            b_name = object_import.import_name(n_block)
            # create mesh data
            b_mesh = bpy.data.meshes.new(b_name)
            # create mesh object and link to data
            b_obj = bpy.data.objects.new(b_name, b_mesh)
            # link mesh object to the scene
            bpy.context.scene.objects.link(b_obj)
            # save original name as object property, for export
            if b_name != n_block.name.decode():
                b_obj.niftools.longname = n_block.name.decode()

            # Mesh hidden flag
            if n_block.flags & 1 == 1:
                b_obj.draw_type = 'WIRE'  # hidden: wire
            else:
                b_obj.draw_type = 'TEXTURED'  # not hidden: shaded

        # set transform matrix for the mesh
        if not applytransform:
            if group_mesh:
                raise nif_utils.NifError("BUG: cannot set matrix when importing meshes in groups; use applytransform = True")

            b_obj.matrix_local = nif_utils.import_matrix(n_block, relative_to=relative_to)

        else:
            # used later on
            transform = nif_utils.import_matrix(n_block, relative_to=relative_to)

        # shortcut for mesh geometry data
        n_data = n_block.data
        if not n_data:
            raise nif_utils.NifError("no shape data in %s" % b_name)

        # vertices
        n_verts = n_data.vertices

        # polygons
        poly_gens = [list(tri) for tri in n_data.get_triangles()]

        # "sticky" UV coordinates: these are transformed in Blender UV's
        n_uv = list()
        for i in range(len(n_data.uv_sets)):
            for lw in range(len(n_data.uv_sets[i])):
                n_uvt = list()
                n_uvt.append(n_data.uv_sets[i][lw].u)
                n_uvt.append(1.0 - n_data.uv_sets[i][lw].v)
                n_uv.append(tuple(n_uvt))
        n_uvco = tuple(n_uv)

        # vertex normals
        n_norms = n_data.normals

        '''
        Properties
        '''
        Property().process_property_list(n_block, b_mesh)

        # TODO [property][material][armature] Reimplement this
        materialIndex = 0

        # v_map will store the vertex index mapping
        # nif vertex i maps to blender vertex v_map[i]
        v_map = [i for i in range(len(n_verts))]  # pre-allocate memory, for faster performance

        # Following code avoids introducing unwanted cracks in UV seams:
        # Construct vertex map to get unique vertex / normal pair list.
        # We use a Python dictionary to remove doubles and to keep track of indices.
        # While we are at it, we also add vertices while constructing the map.
        n_map = {}
        b_v_index = len(b_mesh.vertices)
        for i, v in enumerate(n_verts):
            # The key k identifies unique vertex /normal pairs.
            # We use a tuple of ints for key, this works MUCH faster than a
            # tuple of floats.
            if n_norms:
                n = n_norms[i]
                k = (int(v.x * geometry.VERTEX_RESOLUTION),
                     int(v.y * geometry.VERTEX_RESOLUTION),
                     int(v.z * geometry.VERTEX_RESOLUTION),
                     int(n.x * geometry.NORMAL_RESOLUTION),
                     int(n.y * geometry.NORMAL_RESOLUTION),
                     int(n.z * geometry.NORMAL_RESOLUTION))
            else:
                k = (int(v.x * geometry.VERTEX_RESOLUTION),
                     int(v.y * geometry.VERTEX_RESOLUTION),
                     int(v.z * geometry.VERTEX_RESOLUTION))
            # check if vertex was already added, and if so, what index
            try:
                # this is the bottle neck...
                # can we speed this up?
                if not NifOp.props.combine_vertices:
                    n_map_k = None
                else:
                    n_map_k = n_map[k]
            except KeyError:
                n_map_k = None
            if not n_map_k:
                # not added: new vertex / normal pair
                n_map[k] = i  # unique vertex / normal pair with key k was added, with NIF index i
                v_map[i] = b_v_index  # NIF vertex i maps to blender vertex b_v_index
                # add the vertex
                if applytransform:
                    v = mathutils.Vector([v.x, v.y, v.z])
                    v = v * transform
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = [v.x, v.y, v.z]
                else:
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = [v.x, v.y, v.z]
                # adds normal info if present (Blender recalculates these when
                # switching between edit mode and object mode, handled further)
                # if n_norms:
                #    mv = b_mesh.vertices[b_v_index]
                #    n = n_norms[i]
                #    mv.normal = mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                # NIF vertex i maps to Blender vertex v_map[n_map_k]
                v_map[i] = v_map[n_map_k]
        # report
        NifLog.debug("{0} unique vertex-normal pairs".format(str(len(n_map))))
        # release memory
        del n_map

        # Adds the polygons to the mesh
        f_map = [None] * len(poly_gens)
        b_f_index = len(b_mesh.polygons)
        bf2_index = len(b_mesh.polygons)
        bl_index = len(b_mesh.loops)
        poly_count = len(poly_gens)
        b_mesh.polygons.add(poly_count)
        b_mesh.loops.add(poly_count * 3)
        num_new_faces = 0  # counter for debugging
        unique_faces = list()  # to avoid duplicate polygons
        tri_point_list = list()
        for i, f in enumerate(poly_gens):
            # get face index
            f_verts = [v_map[vert_index] for vert_index in f]
            if tuple(f_verts) in unique_faces:
                continue
            unique_faces.append(tuple(f_verts))
            f_map[i] = b_f_index
            tri_point_list.append(len(poly_gens[i]))
            ls_list = list()
            b_f_index += 1
            num_new_faces += 1
        for ls1 in range(0, num_new_faces * (tri_point_list[len(ls_list)]), (tri_point_list[len(ls_list)])):
            ls_list.append((ls1 + bl_index))
        for i in range(len(unique_faces)):
            if f_map[i] is None:
                continue
            b_mesh.polygons[f_map[i]].loop_start = ls_list[(f_map[i] - bf2_index)]
            b_mesh.polygons[f_map[i]].loop_total = len(unique_faces[(f_map[i] - bf2_index)])
            loop_index = 0
            lp_points = [v_map[loop_point] for loop_point in poly_gens[(f_map[i] - bf2_index)]]
            while loop_index < (len(poly_gens[(f_map[i] - bf2_index)])):
                b_mesh.loops[(loop_index + bl_index)].vertex_index = lp_points[loop_index]
                loop_index += 1
            bl_index += (len(poly_gens[(f_map[i] - bf2_index)]))

        # at this point, deleted polygons (degenerate or duplicate)
        # satisfy f_map[i] = None

        NifLog.debug("{0} unique polygons".format(num_new_faces))

        # set face smoothing and material
        for b_polysmooth_index in f_map:
            if b_polysmooth_index is None:
                continue
            polysmooth = b_mesh.polygons[b_polysmooth_index]
            polysmooth.use_smooth = True if (n_norms or n_block.skin_instance) else False
            # TODO [property][material][armature] This is probably broken, but will only affect armature
            polysmooth.material_index = materialIndex

        Vertex.process_vertex_colors(b_mesh, n_data, v_map)

        if b_mesh.polygons:
            Vertex.process_uv_coordinates(b_mesh, bf2_index, n_uvco, n_data, poly_gens)

        # import skinning info, for meshes affected by bones

        skininst = n_block.skin_instance
        if skininst:
            Skin.process_geometry_skin(b_obj, n_block, skininst, v_map)

        # import morph controller
        # TODO [animation][geometry] move this to import_mesh_controllers
        if NifOp.props.animation:
            b_ipo = GeometryAnimation.process_geometry_animation(applytransform, b_mesh, n_block, transform, v_map)

        # TODO [armature] Maybe move this armature
        # import priority if existing
        if n_block.name in armature.DICT_BONE_PRIORITIES:
            constr = b_obj.constraints.append(bpy.types.Constraint.NULL)
            constr.name = "priority:%i" % armature.DICT_BONE_PRIORITIES[n_block.name]

        # recalculate mesh to render correctly
        # implementation note: update() without validate() can cause crash

        b_mesh.validate()
        b_mesh.update()
        b_obj.select = True
        scn = bpy.context.scene
        scn.objects.active = b_obj

        return b_obj

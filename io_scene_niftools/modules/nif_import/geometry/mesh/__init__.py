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

from itertools import chain

from generated.formats.nif import classes as NifClasses

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_import.animation.morph import MorphAnimation
from io_scene_niftools.modules.nif_import.geometry.vertex.groups import VertexGroup
from io_scene_niftools.modules.nif_import.geometry import mesh
from io_scene_niftools.modules.nif_import.geometry.vertex import Vertex
from io_scene_niftools.modules.nif_import.property.material import Material
from io_scene_niftools.modules.nif_import.property.geometry.mesh import MeshPropertyProcessor
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


class Mesh:

    supported_mesh_types = (NifClasses.BSTriShape, NifClasses.NiMesh, NifClasses.NiTriBasedGeom)

    def __init__(self):
        self.materialhelper = Material()
        self.morph_anim = MorphAnimation()
        self.mesh_prop_processor = MeshPropertyProcessor()

    def import_mesh(self, n_block, b_obj):
        """Creates and returns a raw mesh, or appends geometry data to group_mesh.

        :param n_block: The nif block whose mesh data to import.
        :type n_block: C{NiTriBasedGeom}
        :param b_obj: The mesh to which to append the geometry data. If C{None}, a new mesh is created.
        :type b_obj: A Blender object that has mesh data.
        """

        node_name = n_block.name
        NifLog.info(f"Importing mesh data for geometry '{node_name}'")
        b_mesh = b_obj.data

        assert isinstance(n_block, self.supported_mesh_types)

        vertices = []
        triangles = []
        uvs = None
        vertex_colors = None
        normals = None

        if isinstance(n_block, NifClasses.BSTriShape):
            vertex_attributes = n_block.vertex_desc.vertex_attributes
            vertex_data = n_block.get_vertex_data()
            if isinstance(n_block, NifClasses.BSDynamicTriShape):
                # for BSDynamicTriShapes, the vertex data is stored in 4-component vertices
                vertices = [(vertex.x, vertex.y, vertex.z) for vertex in n_block.vertices]
            elif vertex_attributes.vertex:
                vertices = [vertex.vertex for vertex in vertex_data]
            triangles = n_block.get_triangles()
            if vertex_attributes.u_vs:
                uvs = [[vertex.uv for vertex in vertex_data]]
            if vertex_attributes.vertex_colors:
                vertex_colors = [vertex.vertex_colors for vertex in vertex_data]
            if vertex_attributes.normals:
                normals = [vertex.normal for vertex in vertex_data]
        elif isinstance(n_block, NifClasses.NiMesh):
            # get the data from the associated nidatastreams based on the description in the component semantics
            vertices.extend(list(chain.from_iterable(n_block.geomdata_by_name("POSITION"))))
            vertices.extend(list(chain.from_iterable(n_block.geomdata_by_name("POSITION_BP"))))
            triangles = n_block.get_triangles()
            uvs = n_block.geomdata_by_name("TEXCOORD")
            if len(uvs) == 0:
                uvs = None
            else:
                uvs = [[NifClasses.TexCoord.from_value(tex_coord) for tex_coord in uv_coords] for uv_coords in uvs]
            vertex_colors = n_block.geomdata_by_name("COLOR")
            if len(vertex_colors) == 0:
                vertex_colors = None
            else:
                vertex_colors = list(chain.from_iterable(vertex_colors))
                vertex_colors = [NifClasses.Color4.from_value(color) for color in vertex_colors]
            normals = n_block.geomdata_by_name("NORMAL")
            normals.extend(n_block.geomdata_by_name("NORMAL_BP"))
            if len(normals) == 0:
                normals = None
            else:
                normals = list(chain.from_iterable(normals))
                # for some reason, normals can be four-component structs instead of 3, discard the 4th.
                if len(normals[0]) > 3:
                    normals = [(n[0], n[1], n[2]) for n in normals]
        elif isinstance(n_block, NifClasses.NiTriBasedGeom):

            # shortcut for mesh geometry data
            n_tri_data = n_block.data
            if not n_tri_data:
                raise io_scene_niftools.utils.logging.NifError(f"No shape data in {node_name}")
            vertices = n_tri_data.vertices
            triangles = n_block.get_triangles()
            uvs = n_tri_data.uv_sets
            if n_tri_data.has_vertex_colors:
                vertex_colors = n_tri_data.vertex_colors
            if n_tri_data.has_normals:
                normals = n_tri_data.normals

        # create raw mesh from vertices and triangles
        b_mesh.from_pydata(vertices, [], triangles)
        b_mesh.update()

        # must set faces to smooth before setting custom normals, or the normals bug out!
        is_smooth = True if (not(normals is None) or n_block.is_skin()) else False
        self.set_face_smooth(b_mesh, is_smooth)

        # store additional data layers
        if uvs is not None:
            Vertex.map_uv_layer(b_mesh, uvs)
        if vertex_colors is not None:
            Vertex.map_vertex_colors(b_mesh, vertex_colors)
        if normals is not None:
            Vertex.map_normals(b_mesh, normals)

        self.mesh_prop_processor.process_property_list(n_block, b_obj)

        # import skinning info, for meshes affected by bones
        if n_block.is_skin():
            VertexGroup.import_skin(n_block, b_obj)

        # import morph controller
        if NifOp.props.animation:
            self.morph_anim.import_morph_controller(n_block, b_obj)

        # todo [mesh] remove doubles here using blender operator

    @staticmethod
    def set_face_smooth(b_mesh, smooth):
        """set face smoothing and material"""

        for poly in b_mesh.polygons:
            poly.use_smooth = smooth
            poly.material_index = 0  # only one material

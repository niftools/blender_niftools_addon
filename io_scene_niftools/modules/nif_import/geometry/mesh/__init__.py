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
        assert (isinstance(n_block, NifFormat.NiTriBasedGeom))

        node_name = n_block.name.decode()
        NifLog.info(f"Importing mesh data for geometry '{node_name}'")
        b_mesh = b_obj.data

        # shortcut for mesh geometry data
        n_tri_data = n_block.data
        if not n_tri_data:
            raise io_scene_niftools.utils.logging.NifError(f"No shape data in {node_name}")

        # create raw mesh from vertices and triangles
        b_mesh.from_pydata(n_tri_data.vertices, [], n_tri_data.get_triangles())
        b_mesh.update()

        # must set faces to smooth before setting custom normals, or the normals bug out!
        is_smooth = True if (n_tri_data.has_normals or n_block.skin_instance) else False
        self.set_face_smooth(b_mesh, is_smooth)

        # store additional data layers
        Vertex.map_uv_layer(b_mesh, n_tri_data)
        Vertex.map_vertex_colors(b_mesh, n_tri_data)
        Vertex.map_normals(b_mesh, n_tri_data)

        self.mesh_prop_processor.process_property_list(n_block, b_obj)

        # import skinning info, for meshes affected by bones
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

"""Helper functions to create and test Blender scene geometry data"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005, NIF File Format Library and Tools contributors.
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

import nose

EPSILON = 0.005

"""Vertex coordinates for testing."""
b_verts = {
    (-7.5, 7.5, 3.5),
    (7.5, 3.75, 1.75),
    (7.5, -3.75, -1.75),
    (7.5, 3.75, -1.75),
    (-7.5, 7.5, -3.5),
    (-7.5, -7.5, 3.5),
    (7.5, -3.75, 1.75),
    (-7.5, -7.5, -3.5),
}


def b_create_base_geometry(b_name):
    """Create and return a single polyhedron blender object."""
    b_obj = b_create_cube(b_name)
    return b_obj


def b_create_cube(b_name):
    """Creates prim Cube, single sided"""

    # create a base mesh, and set its name
    bpy.ops.mesh.primitive_cube_add()
    b_obj = bpy.data.objects[bpy.context.active_object.name]
    b_obj.name = b_name

    bpy.ops.object.shade_smooth()
    b_obj.data.show_double_sided = False  # b_mesh default: double sided - true, fix this
    return b_obj


def b_transform_cube(b_obj):
    """ Alters the cube, scaling, transforming """

    b_apply_scale_object()
    b_scale_single_face(b_obj)


def b_apply_scale_object():
    """Scale the currently selected object along each axis."""

    bpy.ops.transform.resize(value=(7.5, 1, 1), constraint_axis=(True, False, False))
    bpy.ops.transform.resize(value=(1, 7.5, 1), constraint_axis=(False, True, False))
    bpy.ops.transform.resize(value=(1, 1, 3.5), constraint_axis=(False, False, True))
    bpy.ops.object.transform_apply(scale=True)


def b_scale_single_face(b_obj):
    """Scale a single face of the object."""

    # scale single face
    for poly in b_obj.data.polygons:
        poly.select = False
    b_obj.data.polygons[2].select = True

    for b_vert_index in b_obj.data.polygons[2].vertices:
        b_obj.data.vertices[b_vert_index].co[1] = b_obj.data.vertices[b_vert_index].co[1] * 0.5
        b_obj.data.vertices[b_vert_index].co[2] = b_obj.data.vertices[b_vert_index].co[2] * 0.5


def b_check_geom_obj(b_obj):
    b_mesh = b_obj.data
    b_check_geom(b_mesh)
    b_check_vertex_count(b_mesh)


def b_check_geom(b_mesh):
    num_triangles = len([face for face in b_mesh.polygons if len(face.vertices) == 3])  # check for tri
    num_triangles += 2 * len([face for face in b_mesh.polygons if len(face.vertices) == 4])  # face = 2 tris
    nose.tools.assert_equal(num_triangles, 12)


def b_check_vertex_count(b_mesh):
    nose.tools.assert_equal(len(b_mesh.vertices), 8)
    verts = {
        tuple(round(co, 4) for co in vert.co)
        for vert in b_mesh.vertices
    }
    nose.tools.assert_set_equal(verts, b_verts)

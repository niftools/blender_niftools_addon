"""This script contains classes to import collision objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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

import operator
from functools import reduce, singledispatch

from pyffi.formats.nif import NifFormat
from pyffi.utils.quickhull import qhull3d

from io_scene_nif.modules.nif_import import collision
from io_scene_nif.modules.nif_import.collision import Collision
from io_scene_nif.modules.nif_import.object import Object
from io_scene_nif.utils import util_consts
from io_scene_nif.utils.util_global import NifData
from io_scene_nif.utils.util_logging import NifLog


class BhkCollision(Collision):

    def __init__(self):
        # dictionary mapping bhkRigidBody objects to objects imported in Blender;
        # we use this dictionary to set the physics constraints (ragdoll etc)
        collision.DICT_HAVOK_OBJECTS = {}

        # TODO [collision][havok][property] Need better way to set this, maybe user property
        if NifData.data._user_version_value_._value == 12 and NifData.data._user_version_2_value_._value == 83:
            self.HAVOK_SCALE = util_consts.HAVOK_SCALE * 10
        else:
            self.HAVOK_SCALE = util_consts.HAVOK_SCALE

        self.process_bhk = singledispatch(self.process_bhk)
        self.register_processors()

    def process_bhk(self, bhk_shape):
        """Base method to warn user that this property is not supported"""
        NifLog.warn("Unsupported bhk shape {0}".format(bhk_shape.__class__.__name__))
        NifLog.warn("This type isn't currently supported: {0}".format(type(bhk_shape)))
        return []

    def register_processors(self):
        """Imports any supported collision shape as list of blender meshes."""
        self.process_bhk.register(NifFormat.bhkTransformShape, self.import_bhktransform)
        self.process_bhk.register(NifFormat.bhkRigidBody, self.import_bhkridgidbody)
        self.process_bhk.register(NifFormat.bhkBoxShape, self.import_bhkbox_shape)
        self.process_bhk.register(NifFormat.bhkSphereShape, self.import_bhksphere_shape)
        self.process_bhk.register(NifFormat.bhkCapsuleShape, self.import_bhkcapsule_shape)
        self.process_bhk.register(NifFormat.bhkConvexVerticesShape, self.import_bhkconvex_vertices_shape)
        self.process_bhk.register(NifFormat.bhkPackedNiTriStripsShape, self.import_bhkpackednitristrips_shape)
        self.process_bhk.register(NifFormat.bhkNiTriStripsShape, self.import_bhk_nitristrips_shape)
        self.process_bhk.register(NifFormat.NiTriStripsData, self.import_nitristrips)
        self.process_bhk.register(NifFormat.bhkMoppBvTreeShape, self.import_bhk_shape)
        self.process_bhk.register(NifFormat.bhkListShape, self.import_bhk_shape)

    def import_bhk_shape(self, bhk_shape):
        return self.process_bhk(bhk_shape)

    def import_bhk_nitristrips_shape(self, bhk_shape):
        self.havok_mat = bhk_shape.material
        return reduce(operator.add, (self.import_bhk_shape(strips) for strips in bhk_shape.strips_data))

    def import_bhk_list_shape(self, bhk_shape):
        return reduce(operator.add, (self.import_bhk_shape(subshape) for subshape in bhk_shape.sub_shapes))

    def import_bhktransform(self, bhkshape):
        """Imports a BhkTransform block and applies the transform to the collision object"""

        # import shapes
        collision_objs = self.import_bhk_shape(bhkshape.shape)
        # find transformation matrix
        transform = mathutils.Matrix(bhkshape.transform.as_list())

        # fix scale
        transform.translation = transform.translation * self.HAVOK_SCALE

        # apply transform
        for b_col_obj in collision_objs:
            b_col_obj.matrix_local = b_col_obj.matrix_local * transform
        # return a list of transformed collision shapes
        return collision_objs

    def import_bhkridgidbody(self, bhkshape):
        """Imports a BhkRigidBody block and applies the transform to the collision objects"""

        # import shapes
        collision_objs = self.import_bhk_shape(bhkshape.shape)

        # find transformation matrix in case of the T version
        if isinstance(bhkshape, NifFormat.bhkRigidBodyT):
            # set rotation
            transform = mathutils.Quaternion([
                bhkshape.rotation.w, bhkshape.rotation.x,
                bhkshape.rotation.y, bhkshape.rotation.z]).to_matrix().to_4x4()

            # set translation
            transform.translation = mathutils.Vector(
                (bhkshape.translation.x,
                 bhkshape.translation.y,
                 bhkshape.translation.z)) * self.HAVOK_SCALE

            # apply transform
            for b_col_obj in collision_objs:
                b_col_obj.matrix_local = b_col_obj.matrix_local * transform

        # set physics flags and mass
        for b_col_obj in collision_objs:
            scn = bpy.context.scene
            scn.objects.active = b_col_obj
            bpy.ops.rigidbody.object_add(type='ACTIVE')
            b_col_obj.rigid_body.enabled = True

            if bhkshape.mass > 0.0001:
                # for physics emulation
                # (mass 0 results in issues with simulation)
                b_col_obj.rigid_body.mass = bhkshape.mass / len(collision_objs)

            b_col_obj.nifcollision.deactivator_type = NifFormat.DeactivatorType._enumkeys[bhkshape.deactivator_type]
            b_col_obj.nifcollision.solver_deactivation = NifFormat.SolverDeactivation._enumkeys[bhkshape.solver_deactivation]
            # b_col_obj.nifcollision.oblivion_layer = NifFormat.OblivionLayer._enumkeys[bhkshape.layer]
            # b_col_obj.nifcollision.quality_type = NifFormat.MotionQuality._enumkeys[bhkshape.quality_type]
            # b_col_obj.nifcollision.motion_system = NifFormat.MotionSystem._enumkeys[bhkshape.motion_system]

            b_col_obj.rigid_body.mass = bhkshape.mass / len(collision_objs)

            b_col_obj.rigid_body.use_deactivation = True
            b_col_obj.rigid_body.friction = bhkshape.friction
            b_col_obj.rigid_body.restitution = bhkshape.restitution
            b_col_obj.rigid_body.linear_damping = bhkshape.linear_damping
            b_col_obj.rigid_body.angular_damping = bhkshape.angular_damping
            b_col_obj.rigid_body.deactivate_linear_velocity = mathutils.Vector([
                bhkshape.linear_velocity.w,
                bhkshape.linear_velocity.x,
                bhkshape.linear_velocity.y,
                bhkshape.linear_velocity.z]).magnitude
            b_col_obj.rigid_body.deactivate_angular_velocity = mathutils.Vector([
                bhkshape.angular_velocity.w,
                bhkshape.angular_velocity.x,
                bhkshape.angular_velocity.y,
                bhkshape.angular_velocity.z]).magnitude

            b_col_obj.collision.permeability = bhkshape.penetration_depth

            b_col_obj.nifcollision.max_linear_velocity = bhkshape.max_linear_velocity
            b_col_obj.nifcollision.max_angular_velocity = bhkshape.max_angular_velocity

            # b_col_obj.nifcollision.col_filter = bhkshape.col_filter

        # import constraints
        # this is done once all objects are imported for now, store all imported havok shapes with object lists
        collision.DICT_HAVOK_OBJECTS[bhkshape] = collision_objs

        # and return a list of transformed collision shapes
        return collision_objs

    def import_bhkbox_shape(self, bhkshape):
        """Import a BhkBox block as a simple Box collision object"""
        # create box
        r = bhkshape.radius * self.HAVOK_SCALE
        minx = -bhkshape.dimensions.x * self.HAVOK_SCALE
        maxx = +bhkshape.dimensions.x * self.HAVOK_SCALE
        miny = -bhkshape.dimensions.y * self.HAVOK_SCALE
        maxy = +bhkshape.dimensions.y * self.HAVOK_SCALE
        minz = -bhkshape.dimensions.z * self.HAVOK_SCALE
        maxz = +bhkshape.dimensions.z * self.HAVOK_SCALE

        # create blender object
        b_obj = Object.box_from_extents("box", minx, maxx, miny, maxy, minz, maxz)
        self.set_b_collider(b_obj, "BOX", r, bhkshape)
        return [b_obj]

    def import_bhksphere_shape(self, bhkshape):
        """Import a BhkSphere block as a simple sphere collision object"""
        r = bhkshape.radius * self.HAVOK_SCALE
        b_obj = Object.box_from_extents("sphere", -r, r, -r, r, -r, r)
        self.set_b_collider(b_obj, "SPHERE", r, bhkshape)
        return [b_obj]

    def import_bhkcapsule_shape(self, bhkshape):
        """Import a BhkCapsule block as a simple cylinder collision object"""
        radius = bhkshape.radius * self.HAVOK_SCALE
        length = (bhkshape.first_point - bhkshape.second_point).norm() * self.HAVOK_SCALE
        first_point = bhkshape.first_point * self.HAVOK_SCALE
        second_point = bhkshape.second_point * self.HAVOK_SCALE
        minx = miny = -radius
        maxx = maxy = +radius
        minz = -radius - length / 2
        maxz = length / 2 + radius

        # create blender object
        b_obj = Object.box_from_extents("capsule", minx, maxx, miny, maxy, minz, maxz)
        # here, these are not encoded as a direction so we must first calculate the direction
        b_obj.matrix_local = self.center_origin_to_matrix(second_point, first_point - second_point)
        # we do it like this so the rigid bodies are correctly drawn in blender
        # because they always draw around the object center
        b_obj.location.z += length / 2
        self.set_b_collider(b_obj, "CAPSULE", radius, bhkshape)
        return [b_obj]

    def import_bhkconvex_vertices_shape(self, bhkshape):
        """Import a BhkConvexVertex block as a convex hull collision object"""

        # find vertices (and fix scale)
        verts, faces = qhull3d([(self.HAVOK_SCALE * n_vert.x,
                                 self.HAVOK_SCALE * n_vert.y,
                                 self.HAVOK_SCALE * n_vert.z)
                                for n_vert in bhkshape.vertices])

        b_obj = Object.mesh_from_data("convexpoly", verts, faces)
        radius = bhkshape.radius * self.HAVOK_SCALE
        self.set_b_collider(b_obj, "BOX", radius, bhkshape)
        b_obj.game.collision_bounds_type = 'CONVEX_HULL'
        return [b_obj]

    def import_bhkpackednitristrips_shape(self, bhkshape):
        """Import a BhkPackedNiTriStrips block as a Triangle-Mesh collision object"""

        # create mesh for each sub shape
        hk_objects = []
        vertex_offset = 0
        subshapes = bhkshape.sub_shapes

        if not subshapes:
            # fallout 3 stores them in the data
            subshapes = bhkshape.data.sub_shapes

        for subshape_num, subshape in enumerate(subshapes):
            verts = []
            faces = []
            for vert_index in range(vertex_offset, vertex_offset + subshape.num_vertices):
                n_vert = bhkshape.data.vertices[vert_index]
                verts.append((n_vert.x * self.HAVOK_SCALE,
                              n_vert.y * self.HAVOK_SCALE,
                              n_vert.z * self.HAVOK_SCALE))

            for hktriangle in bhkshape.data.triangles:
                if (vertex_offset <= hktriangle.triangle.v_1) and (hktriangle.triangle.v_1 < vertex_offset + subshape.num_vertices):
                    faces.append((hktriangle.triangle.v_1 - vertex_offset,
                                  hktriangle.triangle.v_2 - vertex_offset,
                                  hktriangle.triangle.v_3 - vertex_offset))
                else:
                    continue

            b_obj = Object.mesh_from_data('poly%i' % subshape_num, verts, faces)
            radius = min(vert.co.length for vert in b_obj.data.vertices)
            self.set_b_collider(b_obj, "BOX", radius, subshape)
            b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'

            vertex_offset += subshape.num_vertices
            hk_objects.append(b_obj)

        return hk_objects

    def import_nitristrips(self, bhkshape):
        """Import a NiTriStrips block as a Triangle-Mesh collision object"""
        # no factor 7 correction!!!
        verts = [(v.x, v.y, v.z) for v in bhkshape.vertices]
        faces = list(bhkshape.get_triangles())
        b_obj = Object.mesh_from_data("poly", verts, faces)
        # TODO [collision] self.havok_mat!
        self.set_b_collider(b_obj, "BOX", bhkshape.radius)
        b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
        return [b_obj]

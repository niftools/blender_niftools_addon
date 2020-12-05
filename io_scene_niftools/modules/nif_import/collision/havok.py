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

import mathutils

import operator
from functools import reduce, singledispatch

from pyffi.formats.nif import NifFormat
from pyffi.utils.quickhull import qhull3d

from io_scene_niftools.modules.nif_import import collision
from io_scene_niftools.modules.nif_import.collision import Collision
from io_scene_niftools.modules.nif_import.object import Object
from io_scene_niftools.utils import consts
from io_scene_niftools.utils.singleton import NifData
from io_scene_niftools.utils.logging import NifLog


class BhkCollision(Collision):

    def __init__(self):
        # dictionary mapping bhkRigidBody objects to objects imported in Blender;
        # we use this dictionary to set the physics constraints (ragdoll etc)
        collision.DICT_HAVOK_OBJECTS = {}

        # TODO [collision][havok][property] Need better way to set this, maybe user property
        if NifData.data._user_version_value_._value == 12 and NifData.data._user_version_2_value_._value == 83:
            self.HAVOK_SCALE = consts.HAVOK_SCALE * 10
        else:
            self.HAVOK_SCALE = consts.HAVOK_SCALE

        self.process_bhk = singledispatch(self.process_bhk)
        self.process_bhk.register(NifFormat.bhkTransformShape, self.import_bhktransform)
        self.process_bhk.register(NifFormat.bhkRigidBodyT, self.import_bhk_ridgidbody_t)
        self.process_bhk.register(NifFormat.bhkRigidBody, self.import_bhk_ridgid_body)
        self.process_bhk.register(NifFormat.bhkBoxShape, self.import_bhkbox_shape)
        self.process_bhk.register(NifFormat.bhkSphereShape, self.import_bhksphere_shape)
        self.process_bhk.register(NifFormat.bhkCapsuleShape, self.import_bhkcapsule_shape)
        self.process_bhk.register(NifFormat.bhkConvexVerticesShape, self.import_bhkconvex_vertices_shape)
        self.process_bhk.register(NifFormat.bhkPackedNiTriStripsShape, self.import_bhkpackednitristrips_shape)
        self.process_bhk.register(NifFormat.bhkNiTriStripsShape, self.import_bhk_nitristrips_shape)
        self.process_bhk.register(NifFormat.NiTriStripsData, self.import_nitristrips)
        self.process_bhk.register(NifFormat.bhkMoppBvTreeShape, self.import_bhk_mopp_bv_tree_shape)
        self.process_bhk.register(NifFormat.bhkListShape, self.import_bhk_list_shape)
        self.process_bhk.register(NifFormat.bhkSimpleShapePhantom, self.import_bhk_simple_shape_phantom)

    def process_bhk(self, bhk_shape):
        """Base method to warn user that this property is not supported"""
        NifLog.warn(f"Unsupported bhk shape {bhk_shape.__class__.__name__}")
        NifLog.warn(f"This type isn't currently supported: {type(bhk_shape)}")
        return []

    def import_bhk_shape(self, bhk_shape):
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")
        return self.process_bhk(bhk_shape)

    def import_bhk_nitristrips_shape(self, bhk_shape):
        self.havok_mat = bhk_shape.material  # TODO [collision] Havok collision when nif.xml supported.
        return reduce(operator.add, (self.import_bhk_shape(strips) for strips in bhk_shape.strips_data))

    def import_bhk_list_shape(self, bhk_shape):
        return reduce(operator.add, (self.import_bhk_shape(subshape) for subshape in bhk_shape.sub_shapes))

    def import_bhk_mopp_bv_tree_shape(self, bhk_shape):
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")
        return self.process_bhk(bhk_shape.shape)

    def import_bhk_simple_shape_phantom(self, bhkshape):
        """Imports a bhkSimpleShapePhantom block and applies the transform to the collision object"""

        # import shapes
        collision_objs = self.import_bhk_shape(bhkshape.shape)
        NifLog.warn("Support for bhkSimpleShapePhantom is limited, transform is ignored")
        # todo [pyffi/collision] current nifskope shows a transform, our nif xml doesn't, so ignore it for now
        # # find transformation matrix
        # transform = mathutils.Matrix(bhkshape.transform.as_list())
        #
        # # fix scale
        # transform.translation = transform.translation * self.HAVOK_SCALE
        #
        # # apply transform
        # for b_col_obj in collision_objs:
        #     b_col_obj.matrix_local = b_col_obj.matrix_local @ transform
        # return a list of transformed collision shapes
        return collision_objs

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
            b_col_obj.matrix_local = b_col_obj.matrix_local @ transform
        # return a list of transformed collision shapes
        return collision_objs

    def import_bhk_ridgidbody_t(self, bhk_shape):
        """Imports a BhkRigidBody block and applies the transform to the collision objects"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        # import shapes
        collision_objs = self.import_bhk_shape(bhk_shape.shape)

        # find transformation matrix in case of the T version
        # set rotation
        b_rot = bhk_shape.rotation
        transform = mathutils.Quaternion([b_rot.w, b_rot.x, b_rot.y, b_rot.z]).to_matrix().to_4x4()

        # set translation
        b_trans = bhk_shape.translation
        transform.translation = mathutils.Vector((b_trans.x, b_trans.y, b_trans.z)) * self.HAVOK_SCALE

        # apply transform
        for b_col_obj in collision_objs:
            b_col_obj.matrix_local = b_col_obj.matrix_local @ transform

        self._import_bhk_rigid_body(bhk_shape, collision_objs)

        # and return a list of transformed collision shapes
        return collision_objs

    def import_bhk_ridgid_body(self, bhk_shape):
        """Imports a BhkRigidBody block and applies the transform to the collision objects"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        # import shapes
        collision_objs = self.import_bhk_shape(bhk_shape.shape)
        self._import_bhk_rigid_body(bhk_shape, collision_objs)

        # and return a list of transformed collision shapes
        return collision_objs

    def _import_bhk_rigid_body(self, bhkshape, collision_objs):
        # set physics flags and mass
        for b_col_obj in collision_objs:
            b_r_body = b_col_obj.rigid_body

            if bhkshape.mass > 0.0001:
                # for physics emulation
                # (mass 0 results in issues with simulation)
                b_r_body.mass = bhkshape.mass / len(collision_objs)

            b_r_body.mass = bhkshape.mass / len(collision_objs)

            b_r_body.use_deactivation = True
            b_r_body.friction = bhkshape.friction
            b_r_body.restitution = bhkshape.restitution
            b_r_body.linear_damping = bhkshape.linear_damping
            b_r_body.angular_damping = bhkshape.angular_damping
            vel = bhkshape.linear_velocity
            b_r_body.deactivate_linear_velocity = mathutils.Vector([vel.w, vel.x, vel.y, vel.z]).magnitude
            ang_vel = bhkshape.angular_velocity
            b_r_body.deactivate_angular_velocity = mathutils.Vector([ang_vel.w, ang_vel.x, ang_vel.y, ang_vel.z]).magnitude

            # Custom Niftools properties
            b_col_obj.collision.permeability = bhkshape.penetration_depth
            b_col_obj.nifcollision.deactivator_type = NifFormat.DeactivatorType._enumkeys[bhkshape.deactivator_type]
            b_col_obj.nifcollision.solver_deactivation = NifFormat.SolverDeactivation._enumkeys[bhkshape.solver_deactivation]
            b_col_obj.nifcollision.max_linear_velocity = bhkshape.max_linear_velocity
            b_col_obj.nifcollision.max_angular_velocity = bhkshape.max_angular_velocity

            # b_col_obj.nifcollision.oblivion_layer = NifFormat.OblivionLayer._enumkeys[bhkshape.layer]
            # b_col_obj.nifcollision.quality_type = NifFormat.MotionQuality._enumkeys[bhkshape.quality_type]
            # b_col_obj.nifcollision.motion_system = NifFormat.MotionSystem._enumkeys[bhkshape.motion_system]
            # b_col_obj.nifcollision.col_filter = bhkshape.col_filter

        # import constraints
        # this is done once all objects are imported for now, store all imported havok shapes with object lists
        collision.DICT_HAVOK_OBJECTS[bhkshape] = collision_objs

    def import_bhkbox_shape(self, bhk_shape):
        """Import a BhkBox block as a simple Box collision object"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        # create box
        r = bhk_shape.radius * self.HAVOK_SCALE
        dims = bhk_shape.dimensions
        minx = -dims.x * self.HAVOK_SCALE
        maxx = +dims.x * self.HAVOK_SCALE
        miny = -dims.y * self.HAVOK_SCALE
        maxy = +dims.y * self.HAVOK_SCALE
        minz = -dims.z * self.HAVOK_SCALE
        maxz = +dims.z * self.HAVOK_SCALE

        # create blender object
        b_obj = Object.box_from_extents("box", minx, maxx, miny, maxy, minz, maxz)
        self.set_b_collider(b_obj, radius=r, n_obj=bhk_shape)
        return [b_obj]

    def import_bhksphere_shape(self, bhk_shape):
        """Import a BhkSphere block as a simple sphere collision object"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        r = bhk_shape.radius * self.HAVOK_SCALE
        b_obj = Object.box_from_extents("sphere", -r, r, -r, r, -r, r)
        self.set_b_collider(b_obj, display_type="SPHERE", bounds_type='SPHERE', radius=r, n_obj=bhk_shape)
        return [b_obj]

    def import_bhkcapsule_shape(self, bhk_shape):
        """Import a BhkCapsule block as a simple cylinder collision object"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        radius = bhk_shape.radius * self.HAVOK_SCALE
        p_1 = bhk_shape.first_point
        p_2 = bhk_shape.second_point
        length = (p_1 - p_2).norm() * self.HAVOK_SCALE
        first_point = p_1 * self.HAVOK_SCALE
        second_point = p_2 * self.HAVOK_SCALE
        minx = miny = -radius
        maxx = maxy = +radius
        minz = -radius - length / 2
        maxz = length / 2 + radius

        # create blender object
        b_obj = Object.box_from_extents("capsule", minx, maxx, miny, maxy, minz, maxz)
        # here, these are not encoded as a direction so we must first calculate the direction
        b_obj.matrix_local = self.center_origin_to_matrix((first_point + second_point) / 2, first_point - second_point)
        self.set_b_collider(b_obj, bounds_type="CAPSULE", display_type="CAPSULE", radius=radius, n_obj=bhk_shape)
        return [b_obj]

    def import_bhkconvex_vertices_shape(self, bhk_shape):
        """Import a BhkConvexVertex block as a convex hull collision object"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        # find vertices (and fix scale)
        scaled_verts = [(self.HAVOK_SCALE * n_vert.x, self.HAVOK_SCALE * n_vert.y, self.HAVOK_SCALE * n_vert.z)
                        for n_vert in bhk_shape.vertices]
        verts, faces = qhull3d(scaled_verts)

        b_obj = Object.mesh_from_data("convexpoly", verts, faces)
        radius = bhk_shape.radius * self.HAVOK_SCALE
        self.set_b_collider(b_obj, bounds_type="CONVEX_HULL", radius=radius, n_obj=bhk_shape)
        return [b_obj]

    def import_bhkpackednitristrips_shape(self, bhk_shape):
        """Import a BhkPackedNiTriStrips block as a Triangle-Mesh collision object"""
        NifLog.debug(f"Importing {bhk_shape.__class__.__name__}")

        # create mesh for each sub shape
        hk_objects = []
        vertex_offset = 0
        subshapes = bhk_shape.sub_shapes

        if not subshapes:
            # fallout 3 stores them in the data
            subshapes = bhk_shape.data.sub_shapes

        for subshape_num, subshape in enumerate(subshapes):
            verts = []
            faces = []
            for vert_index in range(vertex_offset, vertex_offset + subshape.num_vertices):
                n_vert = bhk_shape.data.vertices[vert_index]
                verts.append((n_vert.x * self.HAVOK_SCALE,
                              n_vert.y * self.HAVOK_SCALE,
                              n_vert.z * self.HAVOK_SCALE))

            for bhk_triangle in bhk_shape.data.triangles:
                bhk_tri = bhk_triangle.triangle
                if (vertex_offset <= bhk_tri.v_1) and (bhk_tri.v_1 < vertex_offset + subshape.num_vertices):
                    faces.append((bhk_tri.v_1 - vertex_offset,
                                  bhk_tri.v_2 - vertex_offset,
                                  bhk_tri.v_3 - vertex_offset))
                else:
                    continue

            b_obj = Object.mesh_from_data(f'poly{subshape_num:d}', verts, faces)
            radius = min(vert.co.length for vert in b_obj.data.vertices)
            self.set_b_collider(b_obj, bounds_type="MESH", radius=radius, n_obj=subshape)

            vertex_offset += subshape.num_vertices
            hk_objects.append(b_obj)

        return hk_objects

    def import_nitristrips(self, bhk_shape):
        """Import a NiTriStrips block as a Triangle-Mesh collision object"""
        # no factor 7 correction!!!
        verts = [(v.x, v.y, v.z) for v in bhk_shape.vertices]
        faces = list(bhk_shape.get_triangles())
        b_obj = Object.mesh_from_data("poly", verts, faces)
        # TODO [collision] self.havok_mat!
        self.set_b_collider(b_obj, bounds_type="MESH", radius=bhk_shape.radius)
        return [b_obj]

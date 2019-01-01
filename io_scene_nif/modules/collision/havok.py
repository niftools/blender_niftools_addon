"""This script contains classes to export havok based collision objects."""

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
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import collision, geometry

import bpy
import mathutils

from io_scene_nif.modules.obj import object_export
from io_scene_nif.modules.obj.blocks import BlockRegistry
from io_scene_nif.nif_common import NifCommon
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


class BHKShape:

    # TODO [collision] Replace hardcoded values either as props, these should be decoded in latest nif.xml latest version
    EXPORT_OB_UNKNOWNBYTE1 = 1
    EXPORT_OB_UNKNOWNBYTE2 = 1
    EXPORT_OB_WIND = 0

    def __init__(self):
        self.HAVOK_SCALE = collision.HAVOK_SCALE

    def export_collision_helper(self, b_obj, parent_block):
        """Helper function to add collision objects to a node. This function
        exports the rigid body, and calls the appropriate function to export
        the collision geometry in the desired format.

        @param b_obj: The object to export as collision.
        @param parent_block: The NiNode parent of the collision.
        """

        # is it packed
        coll_ispacked = (b_obj.game.collision_bounds_type == 'TRIANGLE_MESH')

        # Set Havok Scale ratio
        b_scene = bpy.context.scene.niftools_scene
        if b_scene.user_version == 12:
            if b_scene.user_version_2 == 83:
                self.HAVOK_SCALE = collision.HAVOK_SCALE * 10

        # find physics properties/defaults
        n_havok_mat = b_obj.nifcollision.havok_material
        layer = b_obj.nifcollision.oblivion_layer
        motion_system = b_obj.nifcollision.motion_system
        deactivator_type = b_obj.nifcollision.deactivator_type
        solver_deactivation = b_obj.nifcollision.solver_deactivation
        quality_type = b_obj.nifcollision.quality_type
        mass = b_obj.rigid_body.mass
        restitution = b_obj.rigid_body.restitution
        friction = b_obj.rigid_body.friction
        penetration_depth = b_obj.collision.permeability
        linear_damping = b_obj.rigid_body.linear_damping
        angular_damping = b_obj.rigid_body.angular_damping
        # linear_velocity = b_obj.rigid_body.deactivate_linear_velocity
        # angular_velocity = b_obj.rigid_body.deactivate_angular_velocity
        max_linear_velocity = b_obj.nifcollision.max_linear_velocity
        max_angular_velocity = b_obj.nifcollision.max_angular_velocity
        col_filter = b_obj.nifcollision.col_filter

        # TODO [object][collision][flags] export bsxFlags
        # self.export_bsx_upb_flags(b_obj, parent_block)

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collision_object:
            # note: collision settings are taken from lowerclasschair01.nif
            if layer == "OL_BIPED":
                # special collision object for creatures
                n_col_obj = BlockRegistry.create_block("bhkBlendCollisionObject", b_obj)
                n_col_obj.flags = 9
                n_col_obj.unknown_float_1 = 1.0
                n_col_obj.unknown_float_2 = 1.0
                # also add a controller for it
                blendctrl = BlockRegistry.create_block("bhkBlendController", b_obj)
                blendctrl.flags = 12
                blendctrl.frequency = 1.0
                blendctrl.phase = 0.0
                blendctrl.start_time = NifCommon.FLOAT_MAX
                blendctrl.stop_time = NifCommon.FLOAT_MIN
                parent_block.add_controller(blendctrl)
            else:
                # usual collision object
                n_col_obj = BlockRegistry.create_block("bhkCollisionObject", b_obj)
                if layer == "OL_ANIM_STATIC" and col_filter != 128:
                    # animated collision requires flags = 41
                    # unless it is a constrained but not keyframed object
                    n_col_obj.flags = 41
                else:
                    # in all other cases this seems to be enough
                    n_col_obj.flags = 1

            parent_block.collision_object = n_col_obj
            n_col_obj.target = parent_block
            n_bhkrigidbody = BlockRegistry.create_block("bhkRigidBody", b_obj)
            n_col_obj.body = n_bhkrigidbody
            n_bhkrigidbody.layer = getattr(NifFormat.OblivionLayer, layer)
            n_bhkrigidbody.col_filter = col_filter
            n_bhkrigidbody.unknown_short = 0
            n_bhkrigidbody.unknown_int_1 = 0
            n_bhkrigidbody.unknown_int_2 = 2084020722
            n_bhkrigidbody.unknown_3_ints[0] = 0
            n_bhkrigidbody.unknown_3_ints[1] = 0
            n_bhkrigidbody.unknown_3_ints[2] = 0
            n_bhkrigidbody.collision_response = 1
            n_bhkrigidbody.unknown_byte = 0
            n_bhkrigidbody.process_contact_callback_delay = 65535
            n_bhkrigidbody.unknown_2_shorts[0] = 35899
            n_bhkrigidbody.unknown_2_shorts[1] = 16336
            n_bhkrigidbody.layer_copy = n_bhkrigidbody.layer
            n_bhkrigidbody.col_filter_copy = n_bhkrigidbody.col_filter
            n_bhkrigidbody.unknown_7_shorts[0] = 0
            n_bhkrigidbody.unknown_7_shorts[1] = 21280
            n_bhkrigidbody.unknown_7_shorts[2] = 4581
            n_bhkrigidbody.unknown_7_shorts[3] = 62977
            n_bhkrigidbody.unknown_7_shorts[4] = 65535
            n_bhkrigidbody.unknown_7_shorts[5] = 44
            n_bhkrigidbody.unknown_7_shorts[6] = 0

            # mass is 1.0 at the moment (unless property was set)
            # will be fixed later
            n_bhkrigidbody.mass = mass
            n_bhkrigidbody.linear_damping = linear_damping
            n_bhkrigidbody.angular_damping = angular_damping
            # n_bhkrigidbody.linear_velocity = linear_velocity
            # n_bhkrigidbody.angular_velocity = angular_velocity
            n_bhkrigidbody.friction = friction
            n_bhkrigidbody.restitution = restitution
            n_bhkrigidbody.max_linear_velocity = max_linear_velocity
            n_bhkrigidbody.max_angular_velocity = max_angular_velocity
            n_bhkrigidbody.penetration_depth = penetration_depth
            n_bhkrigidbody.motion_system = motion_system
            n_bhkrigidbody.deactivator_type = deactivator_type
            n_bhkrigidbody.solver_deactivation = solver_deactivation
            n_bhkrigidbody.unknown_byte_1 = self.EXPORT_OB_UNKNOWNBYTE1
            n_bhkrigidbody.unknown_byte_2 = self.EXPORT_OB_UNKNOWNBYTE2
            n_bhkrigidbody.quality_type = quality_type
            n_bhkrigidbody.unknown_int_9 = self.EXPORT_OB_WIND

            # we will use n_col_body to attach shapes to below
            n_col_body = n_bhkrigidbody

        else:
            n_col_body = parent_block.collision_object.body
            # fix total mass
            n_col_body.mass += mass

        if coll_ispacked:
            self.export_collision_packed(b_obj, n_col_body, layer, n_havok_mat)
        else:
            if b_obj.nifcollision.export_bhklist:
                self.export_collision_list(b_obj, n_col_body, layer, n_havok_mat)
            else:
                self.export_collision_single(b_obj, n_col_body, layer, n_havok_mat)

    def export_collision_packed(self, b_obj, n_col_body, layer, n_havok_mat):
        """Add object ob as packed collision object to collision body
        n_col_body. If parent_block hasn't any collisions yet, a new
        packed list is created. If the current collision system is not
        a packed list of collisions (bhkPackedNiTriStripsShape), then
        a ValueError is raised.
        """

        if not n_col_body.shape:

            n_col_mopp = BlockRegistry.create_block("bhkMoppBvTreeShape", b_obj)
            n_col_body.shape = n_col_mopp
            n_col_mopp.material = n_havok_mat
            n_col_mopp.unknown_8_bytes[0] = 160
            n_col_mopp.unknown_8_bytes[1] = 13
            n_col_mopp.unknown_8_bytes[2] = 75
            n_col_mopp.unknown_8_bytes[3] = 1
            n_col_mopp.unknown_8_bytes[4] = 192
            n_col_mopp.unknown_8_bytes[5] = 207
            n_col_mopp.unknown_8_bytes[6] = 144
            n_col_mopp.unknown_8_bytes[7] = 11
            n_col_mopp.unknown_float = 1.0

            # the mopp origin, scale, and data are written later
            n_col_shape = BlockRegistry.create_block("bhkPackedNiTriStripsShape", b_obj)
            n_col_mopp.shape = n_col_shape

            n_col_shape.unknown_int_1 = 0
            n_col_shape.unknown_int_2 = 21929432
            n_col_shape.unknown_float_1 = 0.1
            n_col_shape.unknown_int_3 = 0
            n_col_shape.scale.x = 0
            n_col_shape.scale.y = 0
            n_col_shape.scale.z = 0
            n_col_shape.unknown_float_2 = 0
            n_col_shape.unknown_float_3 = 0.1
            n_col_shape.scale_copy = n_col_shape.scale
            n_col_shape.scale.unknown_float_4 = 0

        else:
            # XXX at the moment, we disable multimaterial mopps
            # XXX do this by raising an exception when trying
            # XXX to add a collision here; code will try to readd it with
            # XXX a fresh NiNode
            raise ValueError('multimaterial mopps not supported for now')
            # TODO [collision] this code will do the trick once multimaterial mopps work
            # n_col_mopp = n_col_body.shape
            # if not isinstance(n_col_mopp, NifFormat.bhkMoppBvTreeShape):
            #     raise ValueError('not a packed list of collisions')
            # n_col_shape = n_col_mopp.shape
            # if not isinstance(n_col_shape, NifFormat.bhkPackedNiTriStripsShape):
            #     raise ValueError('not a packed list of collisions')

        mesh = b_obj.data
        transform = mathutils.Matrix(object_export.get_object_matrix(b_obj, 'localspace').as_list())
        rotation = transform.decompose()[1]

        vertices = [vert.co * transform for vert in mesh.vertices]
        triangles = []
        normals = []
        for face in mesh.polygons:
            if len(face.vertices) < 3:
                continue  # ignore degenerate polygons
            triangles.append([face.vertices[i] for i in (0, 1, 2)])
            normals.append(rotation * face.normal)
            if len(face.vertices) == 4:
                triangles.append([face.vertices[i] for i in (0, 2, 3)])
                normals.append(rotation * face.normal)

        n_col_shape.add_shape(triangles, normals, vertices, layer, n_havok_mat)

    def export_collision_single(self, b_obj, n_col_body, layer, n_havok_mat):
        """Add collision object to n_col_body.
        If n_col_body already has a collision shape, throw ValueError."""
        if n_col_body.shape:
            raise ValueError('collision body already has a shape')
        n_col_body.shape = self.export_collision_object(b_obj, layer, n_havok_mat)

    def export_collision_list(self, b_obj, n_col_body, layer, n_havok_mat):
        """Add collision object obj to the list of collision objects of n_col_body.
        If n_col_body has no collisions yet, a new list is created.
        If the current collision system is not a list of collisions
        (bhkListShape), then a ValueError is raised."""

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody -> bhkListShape
        # (this works in all cases, can be simplified just before
        # the file is written)
        if not n_col_body.shape:
            n_col_shape = BlockRegistry.create_block("bhkListShape")
            n_col_body.shape = n_col_shape
            n_col_shape.material = n_havok_mat
        else:
            n_col_shape = n_col_body.shape
            if not isinstance(n_col_shape, NifFormat.bhkListShape):
                raise ValueError('not a list of collisions')

        n_col_shape.add_shape(self.export_collision_object(b_obj, layer, n_havok_mat))

    def export_collision_object(self, b_obj, layer, n_havok_mat):
        """Export object obj as box, sphere, capsule, or convex hull.
        Note: polyheder is handled by export_collision_packed."""

        # find bounding box data
        if not b_obj.data.vertices:
            NifLog.warn("Skipping collision object {0} without vertices.".format(b_obj))
            return None
        b_vertlist = [vert.co for vert in b_obj.data.vertices]

        minx = min([b_vert[0] for b_vert in b_vertlist])
        miny = min([b_vert[1] for b_vert in b_vertlist])
        minz = min([b_vert[2] for b_vert in b_vertlist])
        maxx = max([b_vert[0] for b_vert in b_vertlist])
        maxy = max([b_vert[1] for b_vert in b_vertlist])
        maxz = max([b_vert[2] for b_vert in b_vertlist])

        calc_bhkshape_radius = (maxx - minx + maxy - miny + maxz - minz) / (6.0 * self.HAVOK_SCALE)
        if b_obj.game.radius - calc_bhkshape_radius > NifOp.props.epsilon:
            radius = calc_bhkshape_radius
        else:
            radius = b_obj.game.radius

        if b_obj.game.collision_bounds_type in {'BOX', 'SPHERE'}:
            # note: collision settings are taken from lowerclasschair01.nif
            coltf = BlockRegistry.create_block("bhkConvexTransformShape", b_obj)
            coltf.material = n_havok_mat
            coltf.unknown_float_1 = 0.1
            coltf.unknown_8_bytes[0] = 96
            coltf.unknown_8_bytes[1] = 120
            coltf.unknown_8_bytes[2] = 53
            coltf.unknown_8_bytes[3] = 19
            coltf.unknown_8_bytes[4] = 24
            coltf.unknown_8_bytes[5] = 9
            coltf.unknown_8_bytes[6] = 253
            coltf.unknown_8_bytes[7] = 4
            hktf = mathutils.Matrix(object_export.get_object_matrix(b_obj, 'localspace').as_list())
            # the translation part must point to the center of the data
            # so calculate the center in local coordinates
            center = mathutils.Vector(((minx + maxx) / 2.0, (miny + maxy) / 2.0, (minz + maxz) / 2.0))
            # and transform it to global coordinates
            center = center * hktf
            hktf[0][3] = center[0]
            hktf[1][3] = center[1]
            hktf[2][3] = center[2]
            # we need to store the transpose of the matrix
            hktf.transpose()
            coltf.transform.set_rows(*hktf)
            # fix matrix for havok coordinate system
            coltf.transform.m_41 /= self.HAVOK_SCALE
            coltf.transform.m_42 /= self.HAVOK_SCALE
            coltf.transform.m_43 /= self.HAVOK_SCALE

            if b_obj.game.collision_bounds_type == 'BOX':
                colbox = BlockRegistry.create_block("bhkBoxShape", b_obj)
                coltf.shape = colbox
                colbox.material = n_havok_mat
                colbox.radius = radius
                colbox.unknown_8_bytes[0] = 0x6b
                colbox.unknown_8_bytes[1] = 0xee
                colbox.unknown_8_bytes[2] = 0x43
                colbox.unknown_8_bytes[3] = 0x40
                colbox.unknown_8_bytes[4] = 0x3a
                colbox.unknown_8_bytes[5] = 0xef
                colbox.unknown_8_bytes[6] = 0x8e
                colbox.unknown_8_bytes[7] = 0x3e
                # fix dimensions for havok coordinate system
                colbox.dimensions.x = (maxx - minx) / (2.0 * self.HAVOK_SCALE)
                colbox.dimensions.y = (maxy - miny) / (2.0 * self.HAVOK_SCALE)
                colbox.dimensions.z = (maxz - minz) / (2.0 * self.HAVOK_SCALE)
                colbox.minimum_size = min(colbox.dimensions.x, colbox.dimensions.y, colbox.dimensions.z)

            elif b_obj.game.collision_bounds_type == 'SPHERE':
                colsphere = BlockRegistry.create_block("bhkSphereShape", b_obj)
                coltf.shape = colsphere
                colsphere.material = n_havok_mat
                # take average radius and
                # TODO [collision] Find out what this is: fix for havok coordinate system (6 * 7 = 42)
                colsphere.radius = radius

            return coltf

        elif b_obj.game.collision_bounds_type in {'CYLINDER', 'CAPSULE'}:
            # take average radius and calculate end points
            local_radius = (maxx + maxy - minx - miny) / 4.0
            transform = b_obj.matrix_local.transposed()
            vert1 = mathutils.Vector([(maxx + minx) / 2.0, (maxy + miny) / 2.0, maxz - local_radius])
            vert2 = mathutils.Vector([(maxx + minx) / 2.0, (maxy + miny) / 2.0, minz + local_radius])
            vert1 = vert1 * transform
            vert2 = vert2 * transform

            # check if end points are far enough from each other
            if (vert1 - vert2).length < NifOp.props.epsilon:
                NifLog.warn("End points of cylinder {0} too close, converting to sphere.".format(b_obj))
                # change type
                b_obj.game.collision_bounds_type = 'SPHERE'
                # instead of duplicating code, just run the function again
                return self.export_collision_object(b_obj, layer, n_havok_mat)

            # end points are ok, so export as capsule
            colcaps = BlockRegistry.create_block("bhkCapsuleShape", b_obj)
            colcaps.material = n_havok_mat
            colcaps.first_point.x = vert1[0] / self.HAVOK_SCALE
            colcaps.first_point.y = vert1[1] / self.HAVOK_SCALE
            colcaps.first_point.z = vert1[2] / self.HAVOK_SCALE
            colcaps.second_point.x = vert2[0] / self.HAVOK_SCALE
            colcaps.second_point.y = vert2[1] / self.HAVOK_SCALE
            colcaps.second_point.z = vert2[2] / self.HAVOK_SCALE

            # set radius, with correct scale
            size_x = b_obj.scale.x
            size_y = b_obj.scale.y

            colcaps.radius = local_radius * (size_x + size_y) * 0.5
            colcaps.radius_1 = colcaps.radius
            colcaps.radius_2 = colcaps.radius

            # fix havok coordinate system for radii
            colcaps.radius /= self.HAVOK_SCALE
            colcaps.radius_1 /= self.HAVOK_SCALE
            colcaps.radius_2 /= self.HAVOK_SCALE
            return colcaps

        elif b_obj.game.collision_bounds_type == 'CONVEX_HULL':
            b_mesh = b_obj.data
            b_transform_mat = mathutils.Matrix(object_export.get_object_matrix(b_obj, 'localspace').as_list())

            b_rot_quat = b_transform_mat.decompose()[1]
            b_scale_vec = b_transform_mat.decompose()[0]

            # TODO [math] Incorporate updates from animation updates

            '''
            scale = math.avg(b_scale_vec.to_tuple())
            if scale < 0:
                scale = - (-scale) ** (1.0 / 3)
            else:
                scale = scale ** (1.0 / 3)
            rotation /= scale
            '''

            # calculate vertices, normals, and distances
            vert_list = [b_transform_mat * vert.co for vert in b_mesh.vertices]
            f_norm_list = [b_rot_quat * b_face.normal for b_face in b_mesh.polygons]
            f_dist_list = [(b_transform_mat * (-1 * b_mesh.vertices[b_mesh.polygons[b_face.index].vertices[0]].co)).dot(
                b_rot_quat.to_matrix() * b_face.normal)
                for b_face in b_mesh.polygons]

            # remove duplicates through dictionary
            vert_dict = {}
            for i, vert in enumerate(vert_list):
                vert_dict[(int(vert[0] * geometry.VERTEX_RESOLUTION),
                           int(vert[1] * geometry.VERTEX_RESOLUTION),
                           int(vert[2] * geometry.VERTEX_RESOLUTION))] = i
            f_dict = {}
            for i, (norm, dist) in enumerate(zip(f_norm_list, f_dist_list)):
                f_dict[(int(norm[0] * geometry.NORMAL_RESOLUTION),
                        int(norm[1] * geometry.NORMAL_RESOLUTION),
                        int(norm[2] * geometry.NORMAL_RESOLUTION),
                        int(dist * geometry.VERTEX_RESOLUTION))] = i
            # sort vertices and normals
            vert_keys = sorted(vert_dict.keys())
            f_keys = sorted(f_dict.keys())
            vert_list = [vert_list[vert_dict[hsh]] for hsh in vert_keys]
            f_norm_list = [f_norm_list[f_dict[hsh]] for hsh in f_keys]
            f_dist_list = [f_dist_list[f_dict[hsh]] for hsh in f_keys]

            if len(f_norm_list) > 65535 or len(vert_list) > 65535:
                raise nif_utils.NifError("ERROR%t|Too many polygons/vertices.\nDecimate/split your b_mesh and try again.")

            col_hull = BlockRegistry.create_block("bhkConvexVerticesShape", b_obj)
            col_hull.material = n_havok_mat
            col_hull.radius = radius
            col_hull.unknown_6_floats[2] = -0.0  # enables arrow detection
            col_hull.unknown_6_floats[5] = -0.0  # enables arrow detection
            # note: unknown 6 floats are usually all 0
            col_hull.num_vertices = len(vert_list)
            col_hull.vertices.update_size()
            for v_hull, vert in zip(col_hull.vertices, vert_list):
                v_hull.x = vert[0] / self.HAVOK_SCALE
                v_hull.y = vert[1] / self.HAVOK_SCALE
                v_hull.z = vert[2] / self.HAVOK_SCALE
                # w component is 0
            col_hull.num_normals = len(f_norm_list)
            col_hull.normals.update_size()
            for n_hull, norm, dist in zip(col_hull.normals, f_norm_list, f_dist_list):
                n_hull.x = norm[0]
                n_hull.y = norm[1]
                n_hull.z = norm[2]
                n_hull.w = dist / self.HAVOK_SCALE

            return col_hull

        else:
            raise nif_utils.NifError("cannot export collision type %s to collision shape list" % b_obj.game.collision_bounds_type)

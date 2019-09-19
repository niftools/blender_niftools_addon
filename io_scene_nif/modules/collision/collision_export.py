"""This script contains classes to export collision objects."""

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
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp


class Collision:
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38

    def __init__(self, parent):
        self.nif_export = parent
        self.HAVOK_SCALE = parent.HAVOK_SCALE

    @staticmethod
    def has_collision():
        """Helper function that determines if a blend file contains a collider."""
        for b_obj in bpy.data.objects:
            if b_obj.game.use_collision_bounds:
                return b_obj

    def export_collision(self, b_obj, n_parent):
        """Main function for adding collision object b_obj to a node."""
        if NifOp.props.game == 'MORROWIND':
            if b_obj.game.collision_bounds_type != 'TRIANGLE_MESH':
                raise nif_utils.NifError("Morrowind only supports Triangle Mesh collisions.")
            node = self.nif_export.objecthelper.create_block("RootCollisionNode", b_obj)
            n_parent.add_child(node)
            node.flags = 0x0003  # default
            self.nif_export.objecthelper.set_object_matrix(b_obj, node)
            for child in b_obj.children:
                self.nif_export.objecthelper.export_node(child, node, None)

        elif NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):

            nodes = [n_parent]
            nodes.extend([block for block in n_parent.children if block.name[:14] == 'collisiondummy'])
            for node in nodes:
                try:
                    self.export_collision_helper(b_obj, node)
                    break
                except ValueError:  # adding collision failed
                    continue
            else:  # all nodes failed so add new one
                node = self.nif_export.objecthelper.create_ninode(b_obj)
                # node.set_transform(self.IDENTITY44)
                node.name = 'collisiondummy%i' % n_parent.num_children
                if b_obj.niftools.objectflags != 0:
                    node_flag_hex = hex(b_obj.niftools.objectflags)
                else:
                    node_flag_hex = 0x000E  # default
                node.flags = node_flag_hex
                n_parent.add_child(node)
                self.export_collision_helper(b_obj, node)

        elif NifOp.props.game in ('ZOO_TYCOON_2',):
            self.export_nicollisiondata(b_obj, n_parent)
        else:
            NifLog.warn(
                "Collisions not supported for game '{0}', skipped collision object '{1}'".format(NifOp.props.game,
                                                                                                 b_obj.name))

    def export_nicollisiondata(self, b_obj, n_parent):
        """ Export b_obj as a NiCollisionData """
        coll_data = self.nif_export.objecthelper.create_block("NiCollisionData", b_obj)
        coll_data.use_abv = 1
        coll_data.target = n_parent
        n_parent.collision_object = coll_data

        bv = coll_data.bounding_volume
        if b_obj.draw_bounds_type == 'SPHERE':
            self.export_spherebv(b_obj, bv)
        elif b_obj.draw_bounds_type == 'BOX':
            self.export_boxbv(b_obj, bv)
        elif b_obj.draw_bounds_type == 'CAPSULE':
            self.export_capsulebv(b_obj, bv)

    def export_spherebv(self, b_obj, bv):
        """ Export b_obj as a NiCollisionData's bounding_volume sphere """

        bv.collision_type = 0
        matrix = self.nif_export.objecthelper.get_object_bind(b_obj)
        center = matrix.translation
        bv.sphere.radius = b_obj.dimensions.x / 2
        bv.sphere.center.x = center.x
        bv.sphere.center.y = center.y
        bv.sphere.center.z = center.z

    def export_boxbv(self, b_obj, bv):
        """ Export b_obj as a NiCollisionData's bounding_volume box """

        bv.collision_type = 1
        matrix = self.nif_export.objecthelper.get_object_bind(b_obj)
        # set center
        center = matrix.translation
        bv.box.center.x = center.x
        bv.box.center.y = center.y
        bv.box.center.z = center.z
        # set axes to unity 3x3 matrix
        bv.box.axis[0].x = 1
        bv.box.axis[1].y = 1
        bv.box.axis[2].z = 1
        # set extent
        extent = b_obj.dimensions / 2
        bv.box.extent[0] = extent.x
        bv.box.extent[1] = extent.y
        bv.box.extent[2] = extent.z

    def export_capsulebv(self, b_obj, bv):
        """ Export b_obj as a NiCollisionData's bounding_volume capsule """

        bv.collision_type = 2
        matrix = self.nif_export.objecthelper.get_object_bind(b_obj)
        offset = matrix.translation
        # calculate the direction unit vector
        dir = (mathutils.Vector((0, 0, 1)) * matrix.to_3x3().inverted()).normalized()
        extent = b_obj.dimensions.z - b_obj.dimensions.x
        radius = b_obj.dimensions.x / 2

        # store data
        bv.capsule.center.x = offset.x
        bv.capsule.center.y = offset.y
        bv.capsule.center.z = offset.z
        bv.capsule.origin.x = dir.x
        bv.capsule.origin.y = dir.y
        bv.capsule.origin.z = dir.z
        # nb properly named in newer nif.xmls
        bv.capsule.unknown_float_1 = extent
        bv.capsule.unknown_float_2 = radius

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
                self.HAVOK_SCALE = self.nif_export.HAVOK_SCALE * 10
            else:
                self.HAVOK_SCALE = self.nif_export.HAVOK_SCALE

        # find physics properties/defaults
        n_havok_mat = (b_obj.nifcollision.havok_material, b_obj.nifcollision.skyrim_havok_material)
        layer = b_obj.nifcollision.oblivion_layer
        motion_system = b_obj.nifcollision.motion_system
        deactivator_type = b_obj.nifcollision.deactivator_type
        solver_deactivation = b_obj.nifcollision.solver_deactivation
        quality_type = b_obj.nifcollision.quality_type
        if not b_obj.rigid_body:
            NifLog.warn("'{0}' has no rigid body, skipping rigid body export".format(b_obj.name))
            return
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

        # Aaron1178 collison stuff
        '''
        #export bsxFlags
        self.export_bsx_upb_flags(b_obj, parent_block)
        '''

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collision_object:
            # note: collision settings are taken from lowerclasschair01.nif
            if layer == "OL_BIPED":
                # special collision object for creatures
                n_col_obj = self.nif_export.objecthelper.create_block("bhkBlendCollisionObject", b_obj)
                n_col_obj.flags = 9
                n_col_obj.unknown_float_1 = 1.0
                n_col_obj.unknown_float_2 = 1.0
                # also add a controller for it
                blendctrl = self.nif_export.objecthelper.create_block("bhkBlendController", b_obj)
                blendctrl.flags = 12
                blendctrl.frequency = 1.0
                blendctrl.phase = 0.0
                blendctrl.start_time = self.FLOAT_MAX
                blendctrl.stop_time = self.FLOAT_MIN
                parent_block.add_controller(blendctrl)
            else:
                # usual collision object
                n_col_obj = self.nif_export.objecthelper.create_block("bhkCollisionObject", b_obj)
                if layer == "OL_ANIM_STATIC" and col_filter != 128:
                    # animated collision requires flags = 41
                    # unless it is a constrainted but not keyframed object
                    n_col_obj.flags = 41
                else:
                    # in all other cases this seems to be enough
                    n_col_obj.flags = 1

            parent_block.collision_object = n_col_obj
            n_col_obj.target = parent_block
            n_bhkrigidbody = self.nif_export.objecthelper.create_block("bhkRigidBody", b_obj)
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

            # mass is 1.0 at the moment (unless property was set on import or by the user)
            # will be fixed in update_rigid_bodies()
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
            # todo [collision / properties / ui] expose unknowns to UI & make sure to keep defaults
            n_bhkrigidbody.unknown_byte_1 = 1
            n_bhkrigidbody.unknown_byte_2 = 1
            n_bhkrigidbody.quality_type = quality_type
            n_bhkrigidbody.unknown_int_9 = 0

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

            n_col_mopp = self.nif_export.objecthelper.create_block("bhkMoppBvTreeShape", b_obj)
            n_col_body.shape = n_col_mopp
            n_col_mopp.material = n_havok_mat[0]
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
            n_col_shape = self.nif_export.objecthelper.create_block("bhkPackedNiTriStripsShape", b_obj)
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
            # XXX this code will do the trick once multimaterial mopps work
            n_col_mopp = n_col_body.shape
            if not isinstance(n_col_mopp, NifFormat.bhkMoppBvTreeShape):
                raise ValueError('not a packed list of collisions')
            n_col_shape = n_col_mopp.shape
            if not isinstance(n_col_shape, NifFormat.bhkPackedNiTriStripsShape):
                raise ValueError('not a packed list of collisions')

        mesh = b_obj.data
        transform = mathutils.Matrix(
            self.nif_export.objecthelper.get_object_matrix(b_obj).as_list())
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
        # (this works in all cases, can be simplified just before the file is written)
        if not n_col_body.shape:
            n_col_shape = self.nif_export.objecthelper.create_block("bhkListShape")
            n_col_body.shape = n_col_shape
            n_col_shape.material = n_havok_mat[0]
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
            coltf = self.nif_export.objecthelper.create_block("bhkConvexTransformShape", b_obj)
            coltf.material = n_havok_mat[0]
            coltf.unknown_float_1 = 0.1
            coltf.unknown_8_bytes[0] = 96
            coltf.unknown_8_bytes[1] = 120
            coltf.unknown_8_bytes[2] = 53
            coltf.unknown_8_bytes[3] = 19
            coltf.unknown_8_bytes[4] = 24
            coltf.unknown_8_bytes[5] = 9
            coltf.unknown_8_bytes[6] = 253
            coltf.unknown_8_bytes[7] = 4
            hktf = mathutils.Matrix(
                self.nif_export.objecthelper.get_object_matrix(b_obj).as_list())
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
                colbox = self.nif_export.objecthelper.create_block("bhkBoxShape", b_obj)
                coltf.shape = colbox
                colbox.material = n_havok_mat[0]
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
                colsphere = self.nif_export.objecthelper.create_block("bhkSphereShape", b_obj)
                coltf.shape = colsphere
                colsphere.material = n_havok_mat[0]
                # take average radius and
                # Todo find out what this is: fix for havok coordinate system (6 * 7 = 42)
                colsphere.radius = radius

            return coltf

        elif b_obj.game.collision_bounds_type in {'CYLINDER', 'CAPSULE'}:

            length = b_obj.dimensions.z - b_obj.dimensions.x
            radius = b_obj.dimensions.x / 2
            matrix = self.nif_export.objecthelper.get_object_bind(b_obj)
            # undo centering on matrix
            matrix.translation.z -= length / 2

            second_point = matrix.translation
            # calculate the direction unit vector
            dir = (mathutils.Vector((0, 0, 1)) * matrix.to_3x3().inverted()).normalized()
            first_point = second_point + dir * length

            radius /= self.HAVOK_SCALE
            first_point /= self.HAVOK_SCALE
            second_point /= self.HAVOK_SCALE

            col_caps = self.nif_export.objecthelper.create_block("bhkCapsuleShape", b_obj)
            col_caps.material = n_havok_mat[0]
            col_caps.skyrim_material = n_havok_mat[1]
            col_caps.first_point.x = first_point.x
            col_caps.first_point.y = first_point.y
            col_caps.first_point.z = first_point.z
            col_caps.second_point.x = second_point.x
            col_caps.second_point.y = second_point.y
            col_caps.second_point.z = second_point.z

            col_caps.radius = radius
            col_caps.radius_1 = radius
            col_caps.radius_2 = radius
            return col_caps

        elif b_obj.game.collision_bounds_type == 'CONVEX_HULL':
            b_mesh = b_obj.data
            b_transform_mat = mathutils.Matrix(self.nif_export.objecthelper.get_object_matrix(b_obj).as_list())

            b_rot_quat = b_transform_mat.decompose()[1]
            b_scale_vec = b_transform_mat.decompose()[0]
            '''
            scale = math.avg(b_scale_vec.to_tuple())
            if scale < 0:
                scale = - (-scale) ** (1.0 / 3)
            else:
                scale = scale ** (1.0 / 3)
            rotation /= scale
            '''

            # calculate vertices, normals, and distances
            vertlist = [b_transform_mat * vert.co for vert in b_mesh.vertices]
            fnormlist = [b_rot_quat * b_face.normal for b_face in b_mesh.polygons]
            fdistlist = [(b_transform_mat * (-1 * b_mesh.vertices[b_mesh.polygons[b_face.index].vertices[0]].co)).dot(
                b_rot_quat.to_matrix() * b_face.normal)
                for b_face in b_mesh.polygons]

            # remove duplicates through dictionary
            vertdict = {}
            for i, vert in enumerate(vertlist):
                vertdict[(int(vert[0] * self.nif_export.VERTEX_RESOLUTION),
                          int(vert[1] * self.nif_export.VERTEX_RESOLUTION),
                          int(vert[2] * self.nif_export.VERTEX_RESOLUTION))] = i
            fdict = {}
            for i, (norm, dist) in enumerate(zip(fnormlist, fdistlist)):
                fdict[(int(norm[0] * self.nif_export.NORMAL_RESOLUTION),
                       int(norm[1] * self.nif_export.NORMAL_RESOLUTION),
                       int(norm[2] * self.nif_export.NORMAL_RESOLUTION),
                       int(dist * self.nif_export.VERTEX_RESOLUTION))] = i
            # sort vertices and normals
            vertkeys = sorted(vertdict.keys())
            fkeys = sorted(fdict.keys())
            vertlist = [vertlist[vertdict[hsh]] for hsh in vertkeys]
            fnormlist = [fnormlist[fdict[hsh]] for hsh in fkeys]
            fdistlist = [fdistlist[fdict[hsh]] for hsh in fkeys]

            if len(fnormlist) > 65535 or len(vertlist) > 65535:
                raise nif_utils.NifError(
                    "ERROR%t|Too many polygons/vertices."
                    " Decimate/split your b_mesh and try again.")

            colhull = self.nif_export.objecthelper.create_block("bhkConvexVerticesShape", b_obj)
            colhull.material = n_havok_mat[0]
            colhull.radius = radius
            colhull.unknown_6_floats[2] = -0.0  # enables arrow detection
            colhull.unknown_6_floats[5] = -0.0  # enables arrow detection
            # note: unknown 6 floats are usually all 0
            colhull.num_vertices = len(vertlist)
            colhull.vertices.update_size()
            for vhull, vert in zip(colhull.vertices, vertlist):
                vhull.x = vert[0] / self.HAVOK_SCALE
                vhull.y = vert[1] / self.HAVOK_SCALE
                vhull.z = vert[2] / self.HAVOK_SCALE
                # w component is 0
            colhull.num_normals = len(fnormlist)
            colhull.normals.update_size()
            for nhull, norm, dist in zip(colhull.normals, fnormlist, fdistlist):
                nhull.x = norm[0]
                nhull.y = norm[1]
                nhull.z = norm[2]
                nhull.w = dist / self.HAVOK_SCALE

            return colhull

        else:
            raise nif_utils.NifError(
                'cannot export collision type %s to collision shape list'
                % b_obj.game.collision_bounds_type)

    def export_bounding_box(self, b_obj, block_parent, bsbound=False):
        """Export a Morrowind or Oblivion bounding box."""
        # calculate bounding box extents
        b_vertlist = [vert.co for vert in b_obj.data.vertices]

        minx = min([b_vert[0] for b_vert in b_vertlist])
        miny = min([b_vert[1] for b_vert in b_vertlist])
        minz = min([b_vert[2] for b_vert in b_vertlist])
        maxx = max([b_vert[0] for b_vert in b_vertlist])
        maxy = max([b_vert[1] for b_vert in b_vertlist])
        maxz = max([b_vert[2] for b_vert in b_vertlist])

        if bsbound:
            n_bbox = self.nif_export.objecthelper.create_block("BSBound")
            # ... the following incurs double scaling because it will be added in
            # both the extra data list and in the old extra data sequence!!!
            # block_parent.add_extra_data(n_bbox)
            # quick hack (better solution would be to make apply_scale non-recursive)
            block_parent.num_extra_data_list += 1
            block_parent.extra_data_list.update_size()
            block_parent.extra_data_list[-1] = n_bbox

            # set name, center, and dimensions
            n_bbox.name = "BBX"
            n_bbox.center.x = b_obj.location[0]
            n_bbox.center.y = b_obj.location[1]
            n_bbox.center.z = b_obj.location[2]
            n_bbox.dimensions.x = (maxx - minx) * b_obj.scale[0] * 0.5
            n_bbox.dimensions.y = (maxy - miny) * b_obj.scale[1] * 0.5
            n_bbox.dimensions.z = (maxz - minz) * b_obj.scale[2] * 0.5

        else:
            n_bbox = self.nif_export.objecthelper.create_ninode()
            block_parent.add_child(n_bbox)
            # set name, flags, translation, and radius
            n_bbox.name = "Bounding Box"
            n_bbox.flags = 4
            n_bbox.translation.x = (minx + maxx) * 0.5 + b_obj.location[0]
            n_bbox.translation.y = (minx + maxx) * 0.5 + b_obj.location[1]
            n_bbox.translation.z = (minx + maxx) * 0.5 + b_obj.location[2]
            n_bbox.rotation.set_identity()
            n_bbox.has_bounding_box = True

            # Ninode's(n_bbox) behaves like a seperate mesh.
            # bounding_box center(n_bbox.bounding_box.translation) is relative to the bound_box
            n_bbox.bounding_box.translation.deepcopy(n_bbox.translation)
            n_bbox.bounding_box.rotation.set_identity()
            n_bbox.bounding_box.radius.x = (maxx - minx) * 0.5
            n_bbox.bounding_box.radius.y = (maxy - miny) * 0.5
            n_bbox.bounding_box.radius.z = (maxz - minz) * 0.5

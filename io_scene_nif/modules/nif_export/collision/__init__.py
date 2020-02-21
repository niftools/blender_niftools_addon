"""This script contains classes to export collision objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2012, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules.nif_export import collision
from io_scene_nif.modules.nif_export.geometry import mesh
from io_scene_nif.modules.nif_export.object.block_registry import block_store
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_logging import NifLog
from io_scene_nif.utils.util_global import NifOp

HAVOK_SCALE = 6.996

# dictionary mapping bhkRigidBody objects to objects imported in Blender;
# we use this dictionary to set the physics constraints (ragdoll etc)
DICT_HAVOK_OBJECTS = {}

IGNORE_BLENDER_PHYSICS = False
EXPORT_BHKLISTSHAPE = False
EXPORT_OB_MASS = 10.0
EXPORT_OB_SOLID = True


class Collision:
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38

    def __init__(self, parent):
        self.objecthelper = parent.objecthelper
        self.HAVOK_SCALE = collision.HAVOK_SCALE

    def export_collision(self, b_obj, n_parent):
        """Main function for adding collision object b_obj to a node."""
        if NifOp.props.game == 'MORROWIND':
            if b_obj.game.collision_bounds_type != 'TRIANGLE_MESH':
                raise util_math.NifError("Morrowind only supports Triangle Mesh collisions.")
            node = block_store.create_block("RootCollisionNode", b_obj)
            n_parent.add_child(node)
            node.flags = 0x0003  # default
            self.objecthelper.set_object_matrix(b_obj, node)
            for child in b_obj.children:
                self.objecthelper.export_node(child, node, None)

        elif NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):

            nodes = [n_parent]
            nodes.extend([block for block in n_parent.children if block.name[:14] == 'collisiondummy'])
            for node in nodes:
                try:
                    self.export_collision_helper(b_obj, node)
                    break
                except ValueError:  # adding collision failed
                    continue
            else:
                # all nodes failed so add new one
                node = self.objecthelper.create_ninode(b_obj)
                # node.set_transform(self.IDENTITY44)
                node.name = 'collisiondummy{:d}'.format(n_parent.num_children)
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
            NifLog.warn("Collisions not supported for game '{0}', skipped collision object '{1}'".format(NifOp.props.game, b_obj.name))

    # TODO [collision] Move to collision
    def update_rigid_bodies(self):
        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            n_rigid_bodies = [n_rigid_body for n_rigid_body in block_store.block_to_obj if isinstance(n_rigid_body, NifFormat.bhkRigidBody)]

            # update rigid body center of gravity and mass
            if collision.IGNORE_BLENDER_PHYSICS:
                # we are not using blender properties to set the mass
                # so calculate mass automatically first calculate distribution of mass
                total_mass = 0
                for n_block in n_rigid_bodies:
                    n_block.update_mass_center_inertia(solid=EXPORT_OB_SOLID)
                    total_mass += n_block.mass

                # to avoid zero division error later (if mass is zero then this does not matter anyway)
                if total_mass == 0:
                    total_mass = 1

                # now update the mass ensuring that total mass is EXPORT_OB_MASS
                for n_block in n_rigid_bodies:
                    mass = EXPORT_OB_MASS * n_block.mass / total_mass
                    # lower bound on mass
                    if mass < 0.0001:
                        mass = 0.05
                    n_block.update_mass_center_inertia(mass=mass, solid=EXPORT_OB_SOLID)
            else:
                # using blender properties, so n_block.mass *should* have been set properly
                for n_block in n_rigid_bodies:
                    # lower bound on mass
                    if n_block.mass < 0.0001:
                        n_block.mass = 0.05
                    n_block.update_mass_center_inertia(mass=n_block.mass, solid=EXPORT_OB_SOLID)

    def export_nicollisiondata(self, b_obj, n_parent):
        """ Export b_obj as a NiCollisionData """
        n_coll_data = block_store.create_block("NiCollisionData", b_obj)
        n_coll_data.use_abv = 1
        n_coll_data.target = n_parent
        n_parent.collision_object = n_coll_data

        n_bv = n_coll_data.bounding_volume
        if b_obj.draw_bounds_type == 'SPHERE':
            self.export_spherebv(b_obj, n_bv)
        elif b_obj.draw_bounds_type == 'BOX':
            self.export_boxbv(b_obj, n_bv)
        elif b_obj.draw_bounds_type == 'CAPSULE':
            self.export_capsulebv(b_obj, n_bv)

    def export_spherebv(self, b_obj, n_bv):
        """ Export b_obj as a NiCollisionData's bounding_volume sphere """

        n_bv.collision_type = 0
        matrix = util_math.get_object_bind(b_obj)
        center = matrix.translation
        n_bv.sphere.radius = b_obj.dimensions.x / 2
        n_bv.sphere.center.x = center.x
        n_bv.sphere.center.y = center.y
        n_bv.sphere.center.z = center.z

    def export_boxbv(self, b_obj, n_bv):
        """ Export b_obj as a NiCollisionData's bounding_volume box """

        n_bv.collision_type = 1
        matrix = util_math.get_object_bind(b_obj)

        # set center
        center = matrix.translation
        n_bv.box.center.x = center.x
        n_bv.box.center.y = center.y
        n_bv.box.center.z = center.z

        # set axes to unity 3x3 matrix
        n_bv.box.axis[0].x = 1
        n_bv.box.axis[1].y = 1
        n_bv.box.axis[2].z = 1

        # set extent
        extent = b_obj.dimensions / 2
        n_bv.box.extent[0] = extent.x
        n_bv.box.extent[1] = extent.y
        n_bv.box.extent[2] = extent.z

    def export_capsulebv(self, b_obj, n_bv):
        """ Export b_obj as a NiCollisionData's bounding_volume capsule """

        n_bv.collision_type = 2
        matrix = util_math.get_object_bind(b_obj)
        offset = matrix.translation
        # calculate the direction unit vector
        v_dir = (mathutils.Vector((0, 0, 1)) * matrix.to_3x3().inverted()).normalized()
        extent = b_obj.dimensions.z - b_obj.dimensions.x
        radius = b_obj.dimensions.x / 2

        # store data
        n_bv.capsule.center.x = offset.x
        n_bv.capsule.center.y = offset.y
        n_bv.capsule.center.z = offset.z
        n_bv.capsule.origin.x = v_dir.x
        n_bv.capsule.origin.y = v_dir.y
        n_bv.capsule.origin.z = v_dir.z
        # TODO [collision] nb properly named in newer nif.xmls
        n_bv.capsule.unknown_float_1 = extent
        n_bv.capsule.unknown_float_2 = radius

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
        if b_scene.user_version == 12 and b_scene.user_version_2 == 83:
            self.HAVOK_SCALE = self.HAVOK_SCALE * 10

        # find physics properties/defaults
        # get havok material name from material name
        if b_obj.data.materials:
            n_havok_mat = b_obj.data.materials[0].name
        else:
            n_havok_mat = "HAV_MAT_STONE"
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

        # TODO [object][collision][flags] export bsxFlags
        # self.export_bsx_upb_flags(b_obj, parent_block)

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collision_object:
            # note: collision settings are taken from lowerclasschair01.nif
            if layer == "OL_BIPED":
                # special collision object for creatures
                n_col_obj = block_store.create_block("bhkBlendCollisionObject", b_obj)
                n_col_obj.flags = 9
                n_col_obj.unknown_float_1 = 1.0
                n_col_obj.unknown_float_2 = 1.0

                # also add a controller for it
                n_blend_ctrl = block_store.create_block("bhkBlendController", b_obj)
                n_blend_ctrl.flags = 12
                n_blend_ctrl.frequency = 1.0
                n_blend_ctrl.phase = 0.0
                n_blend_ctrl.start_time = self.FLOAT_MAX
                n_blend_ctrl.stop_time = self.FLOAT_MIN
                parent_block.add_controller(n_blend_ctrl)
            else:
                # usual collision object
                n_col_obj = block_store.create_block("bhkCollisionObject", b_obj)
                if layer == "OL_ANIM_STATIC" and col_filter != 128:
                    # animated collision requires flags = 41
                    # unless it is a constrainted but not keyframed object
                    n_col_obj.flags = 41
                else:
                    # in all other cases this seems to be enough
                    n_col_obj.flags = 1

            parent_block.collision_object = n_col_obj
            n_col_obj.target = parent_block
            n_bhkrigidbody = block_store.create_block("bhkRigidBody", b_obj)
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

            n_bhkrigidbody.unknown_6_shorts[0] = 21280
            n_bhkrigidbody.unknown_6_shorts[1] = 4581
            n_bhkrigidbody.unknown_6_shorts[2] = 62977
            n_bhkrigidbody.unknown_6_shorts[3] = 65535
            n_bhkrigidbody.unknown_6_shorts[4] = 44
            n_bhkrigidbody.unknown_6_shorts[5] = 0

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
            # TODO [collision][properties][ui] expose unknowns to UI & make sure to keep defaults
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

            n_col_mopp = block_store.create_block("bhkMoppBvTreeShape", b_obj)
            n_col_body.shape = n_col_mopp
            # n_col_mopp.material = n_havok_mat[0]
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
            n_col_shape = block_store.create_block("bhkPackedNiTriStripsShape", b_obj)
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
            raise ValueError('Multi-material mopps not supported for now')
            # TODO [object][collision] this code will do the trick once multi-material mopps work
            n_col_mopp = n_col_body.shape
            if not isinstance(n_col_mopp, NifFormat.bhkMoppBvTreeShape):
                raise ValueError('Not a packed list of collisions')
            n_col_shape = n_col_mopp.shape
            if not isinstance(n_col_shape, NifFormat.bhkPackedNiTriStripsShape):
                raise ValueError('Not a packed list of collisions')

        mesh = b_obj.data
        transform = mathutils.Matrix(self.objecthelper.get_object_matrix(b_obj).as_list())
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
            raise ValueError('Collision body already has a shape')
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
            n_col_shape = block_store.create_block("bhkListShape")
            n_col_body.shape = n_col_shape
            # n_col_shape.material = n_havok_mat[0]
        else:
            n_col_shape = n_col_body.shape
            if not isinstance(n_col_shape, NifFormat.bhkListShape):
                raise ValueError('Not a list of collisions')

        n_col_shape.add_shape(self.export_collision_object(b_obj, layer, n_havok_mat))

    def export_collision_object(self, b_obj, layer, n_havok_mat):
        """Export object obj as box, sphere, capsule, or convex hull.
        Note: polyheder is handled by export_collision_packed."""

        # find bounding box data
        if not b_obj.data.vertices:
            NifLog.warn("Skipping collision object {0} without vertices.".format(b_obj))
            return None

        # TODO [collision] Duplicate code
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
            n_coltf = block_store.create_block("bhkConvexTransformShape", b_obj)

            # n_coltf.material = n_havok_mat[0]
            n_coltf.unknown_float_1 = 0.1
            n_coltf.unknown_8_bytes[0] = 96
            n_coltf.unknown_8_bytes[1] = 120
            n_coltf.unknown_8_bytes[2] = 53
            n_coltf.unknown_8_bytes[3] = 19
            n_coltf.unknown_8_bytes[4] = 24
            n_coltf.unknown_8_bytes[5] = 9
            n_coltf.unknown_8_bytes[6] = 253
            n_coltf.unknown_8_bytes[7] = 4
            hktf = mathutils.Matrix(
                self.objecthelper.get_object_matrix(b_obj).as_list())
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
            n_coltf.transform.set_rows(*hktf)

            # fix matrix for havok coordinate system
            n_coltf.transform.m_41 /= self.HAVOK_SCALE
            n_coltf.transform.m_42 /= self.HAVOK_SCALE
            n_coltf.transform.m_43 /= self.HAVOK_SCALE

            if b_obj.game.collision_bounds_type == 'BOX':
                n_colbox = block_store.create_block("bhkBoxShape", b_obj)
                n_coltf.shape = n_colbox
                # n_colbox.material = n_havok_mat[0]
                n_colbox.radius = radius
                n_colbox.unknown_8_bytes[0] = 0x6b
                n_colbox.unknown_8_bytes[1] = 0xee
                n_colbox.unknown_8_bytes[2] = 0x43
                n_colbox.unknown_8_bytes[3] = 0x40
                n_colbox.unknown_8_bytes[4] = 0x3a
                n_colbox.unknown_8_bytes[5] = 0xef
                n_colbox.unknown_8_bytes[6] = 0x8e
                n_colbox.unknown_8_bytes[7] = 0x3e

                # fix dimensions for havok coordinate system
                n_colbox.dimensions.x = (maxx - minx) / (2.0 * self.HAVOK_SCALE)
                n_colbox.dimensions.y = (maxy - miny) / (2.0 * self.HAVOK_SCALE)
                n_colbox.dimensions.z = (maxz - minz) / (2.0 * self.HAVOK_SCALE)
                n_colbox.minimum_size = min(n_colbox.dimensions.x, n_colbox.dimensions.y, n_colbox.dimensions.z)

            elif b_obj.game.collision_bounds_type == 'SPHERE':
                n_colsphere = block_store.create_block("bhkSphereShape", b_obj)
                n_coltf.shape = n_colsphere
                # n_colsphere.material = n_havok_mat[0]
                # TODO [object][collision] find out what this is: fix for havok coordinate system (6 * 7 = 42)
                # take average radius
                n_colsphere.radius = radius

            return n_coltf

        elif b_obj.game.collision_bounds_type in {'CYLINDER', 'CAPSULE'}:

            length = b_obj.dimensions.z - b_obj.dimensions.x
            radius = b_obj.dimensions.x / 2
            matrix = util_math.get_object_bind(b_obj)

            # undo centering on matrix
            matrix.translation.z -= length / 2

            second_point = matrix.translation

            # calculate the direction unit vector
            v_dir = (mathutils.Vector((0, 0, 1)) * matrix.to_3x3().inverted()).normalized()
            first_point = second_point + v_dir * length

            radius /= self.HAVOK_SCALE
            first_point /= self.HAVOK_SCALE
            second_point /= self.HAVOK_SCALE

            n_col_caps = block_store.create_block("bhkCapsuleShape", b_obj)
            # n_col_caps.material = n_havok_mat[0]
            # n_col_caps.skyrim_material = n_havok_mat[1]
            n_col_caps.first_point.x = first_point.x
            n_col_caps.first_point.y = first_point.y
            n_col_caps.first_point.z = first_point.z
            n_col_caps.second_point.x = second_point.x
            n_col_caps.second_point.y = second_point.y
            n_col_caps.second_point.z = second_point.z

            n_col_caps.radius = radius
            n_col_caps.radius_1 = radius
            n_col_caps.radius_2 = radius
            return n_col_caps

        elif b_obj.game.collision_bounds_type == 'CONVEX_HULL':
            b_mesh = b_obj.data
            b_transform_mat = mathutils.Matrix(self.objecthelper.get_object_matrix(b_obj).as_list())

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
                vertdict[(int(vert[0] * mesh.VERTEX_RESOLUTION),
                          int(vert[1] * mesh.VERTEX_RESOLUTION),
                          int(vert[2] * mesh.VERTEX_RESOLUTION))] = i
            fdict = {}
            for i, (norm, dist) in enumerate(zip(fnormlist, fdistlist)):
                fdict[(int(norm[0] * mesh.NORMAL_RESOLUTION),
                       int(norm[1] * mesh.NORMAL_RESOLUTION),
                       int(norm[2] * mesh.NORMAL_RESOLUTION),
                       int(dist * mesh.VERTEX_RESOLUTION))] = i

            # sort vertices and normals
            vertkeys = sorted(vertdict.keys())
            fkeys = sorted(fdict.keys())
            vertlist = [vertlist[vertdict[hsh]] for hsh in vertkeys]
            fnormlist = [fnormlist[fdict[hsh]] for hsh in fkeys]
            fdistlist = [fdistlist[fdict[hsh]] for hsh in fkeys]

            if len(fnormlist) > 65535 or len(vertlist) > 65535:
                raise util_math.NifError("Mesh has too many polygons/vertices. Simply/split your mesh and try again.")

            colhull = block_store.create_block("bhkConvexVerticesShape", b_obj)
            # colhull.material = n_havok_mat[0]
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
            raise util_math.NifError('Cannot export collision type %s to collision shape list'.format(b_obj.game.collision_bounds_type))


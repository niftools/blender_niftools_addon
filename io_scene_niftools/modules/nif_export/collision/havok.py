"""Script to export havok collisions."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export.collision import Collision
from io_scene_niftools.utils import math, consts
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


class BhkCollision(Collision):

    IGNORE_BLENDER_PHYSICS = False
    EXPORT_BHKLISTSHAPE = False
    EXPORT_OB_MASS = 10.0
    EXPORT_OB_SOLID = True

    def __init__(self):
        self.HAVOK_SCALE = consts.HAVOK_SCALE

    def export_collision_helper(self, b_obj, parent_block):
        """Helper function to add collision objects to a node. This function
        exports the rigid body, and calls the appropriate function to export
        the collision geometry in the desired format.

        @param b_obj: The object to export as collision.
        @param parent_block: The NiNode parent of the collision.
        """

        rigid_body = b_obj.rigid_body
        if not rigid_body:
            NifLog.warn(f"'{b_obj.name}' has no rigid body, skipping rigid body export")
            return

        # is it packed
        coll_ispacked = (rigid_body.collision_shape == 'MESH')

        # Set Havok Scale ratio
        b_scene = bpy.context.scene.niftools_scene
        if b_scene.user_version == 12 and b_scene.user_version_2 == 83:
            self.HAVOK_SCALE = consts.HAVOK_SCALE * 10

        # find physics properties/defaults
        # get havok material name from material name
        if b_obj.data.materials:
            n_havok_mat = b_obj.data.materials[0].name
        else:
            n_havok_mat = "HAV_MAT_STONE"

        # linear_velocity = b_obj.rigid_body.deactivate_linear_velocity
        # angular_velocity = b_obj.rigid_body.deactivate_angular_velocity
        layer = b_obj.nifcollision.oblivion_layer

        # TODO [object][collision][flags] export bsxFlags
        # self.export_bsx_upb_flags(b_obj, parent_block)

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collision_object:
            # note: collision settings are taken from lowerclasschair01.nif
            if layer == "OL_BIPED":
                # special collision object for creatures
                n_col_obj = self.export_bhk_blend_collision(b_obj)

                # TODO [collsion][annimation] add detection for this
                self.export_bhk_blend_controller(b_obj, parent_block)
            else:
                # usual collision object
                n_col_obj = self.export_bhk_collison_object(b_obj)

            parent_block.collision_object = n_col_obj
            n_col_obj.target = parent_block

            n_bhkrigidbody = self.export_bhk_rigid_body(b_obj, n_col_obj)

            # we will use n_col_body to attach shapes to below
            n_col_body = n_bhkrigidbody

        else:
            n_col_body = parent_block.collision_object.body
            # fix total mass
            n_col_body.mass += rigid_body.mass

        if coll_ispacked:
            self.export_collision_packed(b_obj, n_col_body, layer, n_havok_mat)
        else:
            if b_obj.nifcollision.export_bhklist:
                self.export_collision_list(b_obj, n_col_body, layer, n_havok_mat)
            else:
                self.export_collision_single(b_obj, n_col_body, layer, n_havok_mat)

    def export_bhk_rigid_body(self, b_obj, n_col_obj):

        n_r_body = block_store.create_block("bhkRigidBody", b_obj)
        n_col_obj.body = n_r_body
        n_r_body.layer = getattr(NifFormat.OblivionLayer, b_obj.nifcollision.oblivion_layer)
        n_r_body.col_filter = b_obj.nifcollision.col_filter
        n_r_body.unknown_short = 0
        n_r_body.unknown_int_1 = 0
        n_r_body.unknown_int_2 = 2084020722
        unk_3 = n_r_body.unknown_3_ints
        unk_3[0] = 0
        unk_3[1] = 0
        unk_3[2] = 0
        n_r_body.collision_response = 1
        n_r_body.unknown_byte = 0
        n_r_body.process_contact_callback_delay = 65535
        unk_2 = n_r_body.unknown_2_shorts
        unk_2[0] = 35899
        unk_2[1] = 16336
        n_r_body.layer_copy = n_r_body.layer
        n_r_body.col_filter_copy = n_r_body.col_filter
        # TODO [format] nif.xml update required
        # ukn_6 = n_r_body.unknown_6_shorts
        # ukn_6[0] = 21280
        # ukn_6[1] = 4581
        # ukn_6[2] = 62977
        # ukn_6[3] = 65535
        # ukn_6[4] = 44
        # ukn_6[5] = 0

        b_r_body = b_obj.rigid_body
        # mass is 1.0 at the moment (unless property was set on import or by the user)
        # will be fixed in update_rigid_bodies()
        n_r_body.mass = b_r_body.mass
        n_r_body.linear_damping = b_r_body.linear_damping
        n_r_body.angular_damping = b_r_body.angular_damping
        # n_r_body.linear_velocity = linear_velocity
        # n_r_body.angular_velocity = angular_velocity
        n_r_body.friction = b_r_body.friction
        n_r_body.restitution = b_r_body.restitution
        n_r_body.max_linear_velocity = b_obj.nifcollision.max_linear_velocity
        n_r_body.max_angular_velocity = b_obj.nifcollision.max_angular_velocity
        n_r_body.penetration_depth = b_obj.collision.permeability
        n_r_body.motion_system = b_obj.nifcollision.motion_system
        n_r_body.deactivator_type = b_obj.nifcollision.deactivator_type
        n_r_body.solver_deactivation = b_obj.nifcollision.solver_deactivation
        # TODO [collision][properties][ui] expose unknowns to UI & make sure to keep defaults
        n_r_body.unknown_byte_1 = 1
        n_r_body.unknown_byte_2 = 1
        n_r_body.quality_type = b_obj.nifcollision.quality_type
        n_r_body.unknown_int_9 = 0
        return n_r_body

    def export_bhk_collison_object(self, b_obj):
        layer = b_obj.nifcollision.oblivion_layer
        col_filter = b_obj.nifcollision.col_filter

        n_col_obj = block_store.create_block("bhkCollisionObject", b_obj)
        if layer == "OL_ANIM_STATIC" and col_filter != 128:
            # animated collision requires flags = 41
            # unless it is a constrainted but not keyframed object
            n_col_obj.flags = 41
        else:
            # in all other cases this seems to be enough
            n_col_obj.flags = 1
        return n_col_obj

    def export_bhk_blend_collision(self, b_obj):
        n_col_obj = block_store.create_block("bhkBlendCollisionObject", b_obj)
        n_col_obj.flags = 9
        n_col_obj.unknown_float_1 = 1.0
        n_col_obj.unknown_float_2 = 1.0
        return n_col_obj

    # TODO [collision][animation] Move out to an physic animation class.
    def export_bhk_blend_controller(self, b_obj, parent_block):
        # also add a controller for it
        n_blend_ctrl = block_store.create_block("bhkBlendController", b_obj)
        n_blend_ctrl.flags = 12
        n_blend_ctrl.frequency = 1.0
        n_blend_ctrl.phase = 0.0
        n_blend_ctrl.start_time = consts.FLOAT_MAX
        n_blend_ctrl.stop_time = consts.FLOAT_MIN
        parent_block.add_controller(n_blend_ctrl)

    # TODO [collision] Move to collision
    def update_rigid_bodies(self):
        if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            n_rigid_bodies = [n_rigid_body for n_rigid_body in block_store.block_to_obj if isinstance(n_rigid_body, NifFormat.bhkRigidBody)]

            # update rigid body center of gravity and mass
            if self.IGNORE_BLENDER_PHYSICS:
                # we are not using blender properties to set the mass
                # so calculate mass automatically first calculate distribution of mass
                total_mass = 0
                for n_block in n_rigid_bodies:
                    n_block.update_mass_center_inertia(solid=self.EXPORT_OB_SOLID)
                    total_mass += n_block.mass

                # to avoid zero division error later (if mass is zero then this does not matter anyway)
                if total_mass == 0:
                    total_mass = 1

                # now update the mass ensuring that total mass is EXPORT_OB_MASS
                for n_block in n_rigid_bodies:
                    mass = self.EXPORT_OB_MASS * n_block.mass / total_mass
                    # lower bound on mass
                    if mass < 0.0001:
                        mass = 0.05
                    n_block.update_mass_center_inertia(mass=mass, solid=self.EXPORT_OB_SOLID)
            else:
                # using blender properties, so n_block.mass *should* have been set properly
                for n_block in n_rigid_bodies:
                    # lower bound on mass
                    if n_block.mass < 0.0001:
                        n_block.mass = 0.05
                    n_block.update_mass_center_inertia(mass=n_block.mass, solid=self.EXPORT_OB_SOLID)

    def export_bhk_mopp_bv_tree_shape(self, b_obj, n_col_body):
        n_col_mopp = block_store.create_block("bhkMoppBvTreeShape", b_obj)
        n_col_body.shape = n_col_mopp
        # n_col_mopp.material = n_havok_mat[0]
        unk_8 = n_col_mopp.unknown_8_bytes
        unk_8[0] = 160
        unk_8[1] = 13
        unk_8[2] = 75
        unk_8[3] = 1
        unk_8[4] = 192
        unk_8[5] = 207
        unk_8[6] = 144
        unk_8[7] = 11
        n_col_mopp.unknown_float = 1.0
        return n_col_mopp

    def export_bhk_packed_nitristrip_shape(self, b_obj, n_col_mopp):
        # the mopp origin, scale, and data are written later
        n_col_shape = block_store.create_block("bhkPackedNiTriStripsShape", b_obj)
        n_col_shape.unknown_int_1 = 0
        n_col_shape.unknown_int_2 = 21929432
        n_col_shape.unknown_float_1 = 0.1
        n_col_shape.unknown_int_3 = 0
        n_col_shape.unknown_float_2 = 0
        n_col_shape.unknown_float_3 = 0.1
        scale = n_col_shape.scale
        scale.x = 0
        scale.y = 0
        scale.z = 0
        scale.unknown_float_4 = 0
        n_col_shape.scale_copy = scale
        n_col_mopp.shape = n_col_shape
        return n_col_shape

    def export_bhk_convex_vertices_shape(self, b_obj, fdistlist, fnormlist, radius, vertlist):
        colhull = block_store.create_block("bhkConvexVerticesShape", b_obj)
        # colhull.material = n_havok_mat[0]
        colhull.radius = radius

        unk_6 = colhull.unknown_6_floats
        unk_6[2] = -0.0  # enables arrow detection
        unk_6[5] = -0.0  # enables arrow detection
        # note: unknown 6 floats are usually all 0

        # Vertices
        colhull.num_vertices = len(vertlist)
        colhull.vertices.update_size()
        for vhull, vert in zip(colhull.vertices, vertlist):
            vhull.x = vert[0] / self.HAVOK_SCALE
            vhull.y = vert[1] / self.HAVOK_SCALE
            vhull.z = vert[2] / self.HAVOK_SCALE
            # w component is 0

        # Normals
        colhull.num_normals = len(fnormlist)
        colhull.normals.update_size()
        for nhull, norm, dist in zip(colhull.normals, fnormlist, fdistlist):
            nhull.x = norm[0]
            nhull.y = norm[1]
            nhull.z = norm[2]
            nhull.w = dist / self.HAVOK_SCALE

        return colhull

    def export_collision_object(self, b_obj, layer, n_havok_mat):
        """Export object obj as box, sphere, capsule, or convex hull.
        Note: polyheder is handled by export_collision_packed."""

        # find bounding box data
        if not b_obj.data.vertices:
            NifLog.warn(f"Skipping collision object {b_obj} without vertices.")
            return None

        box_extends = self.calculate_box_extents(b_obj)
        calc_bhkshape_radius = (box_extends[0][1] - box_extends[0][0] +
                                box_extends[1][1] - box_extends[1][0] +
                                box_extends[2][1] - box_extends[2][0]) / (6.0 * self.HAVOK_SCALE)

        b_r_body = b_obj.rigid_body
        if b_r_body.use_margin:
            margin = b_r_body.collision_margin
            if margin - calc_bhkshape_radius > NifOp.props.epsilon:
                radius = calc_bhkshape_radius
            else:
                radius = margin

        collision_shape = b_r_body.collision_shape
        if collision_shape in {'BOX', 'SPHERE'}:
            # note: collision settings are taken from lowerclasschair01.nif
            n_coltf = block_store.create_block("bhkConvexTransformShape", b_obj)

            # n_coltf.material = n_havok_mat[0]
            n_coltf.unknown_float_1 = 0.1

            unk_8 = n_coltf.unknown_8_bytes
            unk_8[0] = 96
            unk_8[1] = 120
            unk_8[2] = 53
            unk_8[3] = 19
            unk_8[4] = 24
            unk_8[5] = 9
            unk_8[6] = 253
            unk_8[7] = 4

            hktf = mathutils.Matrix(math.get_object_matrix(b_obj).as_list())
            # the translation part must point to the center of the data
            # so calculate the center in local coordinates

            # TODO [collsion] Replace when method moves to bound class, causes circular dependency
            center = mathutils.Vector(((box_extends[0][0] + box_extends[0][1]) / 2.0,
                                      (box_extends[1][0] + box_extends[1][1]) / 2.0,
                                      (box_extends[2][0] + box_extends[2][1]) / 2.0))

            # and transform it to global coordinates
            center = center @ hktf
            hktf[0][3] = center[0]
            hktf[1][3] = center[1]
            hktf[2][3] = center[2]

            # we need to store the transpose of the matrix
            hktf.transpose()
            n_coltf.transform.set_rows(*hktf)

            # fix matrix for havok coordinate system
            n_coltf.transform.m_14 /= self.HAVOK_SCALE
            n_coltf.transform.m_24 /= self.HAVOK_SCALE
            n_coltf.transform.m_34 /= self.HAVOK_SCALE

            if collision_shape == 'BOX':
                n_colbox = block_store.create_block("bhkBoxShape", b_obj)
                n_coltf.shape = n_colbox
                # n_colbox.material = n_havok_mat[0]
                n_colbox.radius = radius

                unk_8 = n_colbox.unknown_8_bytes
                unk_8[0] = 0x6b
                unk_8[1] = 0xee
                unk_8[2] = 0x43
                unk_8[3] = 0x40
                unk_8[4] = 0x3a
                unk_8[5] = 0xef
                unk_8[6] = 0x8e
                unk_8[7] = 0x3e

                # fix dimensions for havok coordinate system
                box_extends = self.calculate_box_extents(b_obj)
                dims = n_colbox.dimensions
                dims.x = (box_extends[0][1] - box_extends[0][0]) / (2.0 * self.HAVOK_SCALE)
                dims.y = (box_extends[1][1] - box_extends[1][0]) / (2.0 * self.HAVOK_SCALE)
                dims.z = (box_extends[2][1] - box_extends[2][0]) / (2.0 * self.HAVOK_SCALE)
                n_colbox.minimum_size = min(dims.x, dims.y, dims.z)

            elif collision_shape == 'SPHERE':
                n_colsphere = block_store.create_block("bhkSphereShape", b_obj)
                n_coltf.shape = n_colsphere
                # n_colsphere.material = n_havok_mat[0]
                # TODO [object][collision] find out what this is: fix for havok coordinate system (6 * 7 = 42)
                # take average radius
                n_colsphere.radius = radius

            return n_coltf

        elif collision_shape in {'CYLINDER', 'CAPSULE'}:

            length = b_obj.dimensions.z - b_obj.dimensions.x
            radius = b_obj.dimensions.x / 2
            matrix = math.get_object_bind(b_obj)

            length_half = length / 2
            # calculate the direction unit vector
            v_dir = (mathutils.Vector((0, 0, 1)) @ matrix.to_3x3().inverted()).normalized()
            first_point = matrix.translation + v_dir * length_half
            second_point = matrix.translation - v_dir * length_half

            radius /= self.HAVOK_SCALE
            first_point /= self.HAVOK_SCALE
            second_point /= self.HAVOK_SCALE

            n_col_caps = block_store.create_block("bhkCapsuleShape", b_obj)
            # n_col_caps.material = n_havok_mat[0]
            # n_col_caps.skyrim_material = n_havok_mat[1]

            cap_1 = n_col_caps.first_point
            cap_1.x = first_point.x
            cap_1.y = first_point.y
            cap_1.z = first_point.z

            cap_2 = n_col_caps.second_point
            cap_2.x = second_point.x
            cap_2.y = second_point.y
            cap_2.z = second_point.z

            n_col_caps.radius = radius
            n_col_caps.radius_1 = radius
            n_col_caps.radius_2 = radius
            return n_col_caps

        elif collision_shape == 'CONVEX_HULL':
            b_mesh = b_obj.data
            b_transform_mat = mathutils.Matrix(math.get_object_matrix(b_obj).as_list())

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
            vertlist = [b_transform_mat @ vert.co for vert in b_mesh.vertices]
            fnormlist = [b_rot_quat @ b_face.normal for b_face in b_mesh.polygons]
            fdistlist = [(b_transform_mat @ (-1 * b_mesh.vertices[b_mesh.polygons[b_face.index].vertices[0]].co)).dot(b_rot_quat.to_matrix() @ b_face.normal) for b_face in b_mesh.polygons]

            # remove duplicates through dictionary
            vertdict = {}
            for i, vert in enumerate(vertlist):
                vertdict[(int(vert[0] * consts.VERTEX_RESOLUTION),
                          int(vert[1] * consts.VERTEX_RESOLUTION),
                          int(vert[2] * consts.VERTEX_RESOLUTION))] = i

            fdict = {}
            for i, (norm, dist) in enumerate(zip(fnormlist, fdistlist)):
                fdict[(int(norm[0] * consts.NORMAL_RESOLUTION),
                       int(norm[1] * consts.NORMAL_RESOLUTION),
                       int(norm[2] * consts.NORMAL_RESOLUTION),
                       int(dist * consts.VERTEX_RESOLUTION))] = i

            # sort vertices and normals
            vertkeys = sorted(vertdict.keys())
            fkeys = sorted(fdict.keys())
            vertlist = [vertlist[vertdict[hsh]] for hsh in vertkeys]
            fnormlist = [fnormlist[fdict[hsh]] for hsh in fkeys]
            fdistlist = [fdistlist[fdict[hsh]] for hsh in fkeys]

            if len(fnormlist) > 65535 or len(vertlist) > 65535:
                raise io_scene_niftools.utils.logging.NifError("Mesh has too many polygons/vertices. Simply/split your mesh and try again.")

            return self.export_bhk_convex_vertices_shape(b_obj, fdistlist, fnormlist, radius, vertlist)

        else:
            raise io_scene_niftools.utils.logging.NifError(f'Cannot export collision type {collision_shape} to collision shape list')

    def export_collision_packed(self, b_obj, n_col_body, layer, n_havok_mat):
        """Add object ob as packed collision object to collision body
        n_col_body. If parent_block hasn't any collisions yet, a new
        packed list is created. If the current collision system is not
        a packed list of collisions (bhkPackedNiTriStripsShape), then
        a ValueError is raised.
        """

        if not n_col_body.shape:

            n_col_mopp = self.export_bhk_mopp_bv_tree_shape(b_obj, n_col_body)
            n_col_shape = self.export_bhk_packed_nitristrip_shape(b_obj, n_col_mopp)

        else:
            raise ValueError('Multi-material mopps not supported for now')
            # TODO [object][collision] this code will do the trick once multi-material mopps work
            # n_col_mopp = n_col_body.shape
            # if not isinstance(n_col_mopp, NifFormat.bhkMoppBvTreeShape):
            #     raise ValueError('Not a packed list of collisions')
            # n_col_shape = n_col_mopp.shape
            # if not isinstance(n_col_shape, NifFormat.bhkPackedNiTriStripsShape):
            #     raise ValueError('Not a packed list of collisions')

        b_mesh = b_obj.data
        transform = mathutils.Matrix(math.get_object_matrix(b_obj).as_list())
        rotation = transform.decompose()[1]

        vertices = [vert.co * transform for vert in b_mesh.vertices]
        triangles = []
        normals = []
        for face in b_mesh.polygons:
            if len(face.vertices) < 3:
                continue  # ignore degenerate polygons
            triangles.append([face.vertices[i] for i in (0, 1, 2)])
            normals.append(rotation * face.normal)
            if len(face.vertices) == 4:
                triangles.append([face.vertices[i] for i in (0, 2, 3)])
                normals.append(rotation * face.normal)

        # TODO [collision][havok] Redo this as a material lookup
        havok_mat = NifFormat.HavokMaterial()
        havok_mat.material = n_havok_mat
        n_col_shape.add_shape(triangles, normals, vertices, layer, havok_mat.material)

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

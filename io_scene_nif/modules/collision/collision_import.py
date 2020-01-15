"""This script contains classes to import collision objects."""

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

from functools import reduce
import operator

from pyffi.formats.nif import NifFormat
from pyffi.utils.quickhull import qhull3d

from io_scene_nif.modules import collision
from io_scene_nif.modules.nif_import.object import Object
from io_scene_nif.utility.util_logging import NifLog
from io_scene_nif.utility.util_global import NifData


def get_material(mat_name):
    """Returns material of mat_name, create new one if required"""
    if mat_name not in bpy.data.materials:
        bpy.data.materials.new(mat_name)
    return bpy.data.materials[mat_name]


class Collision:
    """Import basic and Havok Collision Shapes"""

    def __init__(self):
        # dictionary mapping bhkRigidBody objects to objects imported in Blender;
        # we use this dictionary to set the physics constraints (ragdoll etc)
        collision.DICT_HAVOK_OBJECTS = {}

        # TODO [collision][havok][property] Need better way to set this, maybe user property
        if NifData.data._user_version_value_._value == 12 and NifData.data._user_version_2_value_._value == 83:
            self.HAVOK_SCALE = collision.HAVOK_SCALE * 10
        else:
            self.HAVOK_SCALE = collision.HAVOK_SCALE

    def import_collision(self, n_node):
        """ Imports a NiNode's collision_object, if present"""
        if n_node.collision_object:
            if isinstance(n_node.collision_object, NifFormat.bhkNiCollisionObject):
                return self.import_bhk_shape(n_node.collision_object.body)
            elif isinstance(n_node.collision_object, NifFormat.NiCollisionData):
                return self.import_bounding_volume(n_node.collision_object.bounding_volume)
        return []

    def set_b_collider(self, b_obj, bounds_type, radius, n_obj=None):
        """ Helper function to set up b_obj so it becomes recognizable as a collision object """
        # set bounds type
        b_obj.draw_type = 'BOUNDS'
        # b_obj.show_bounds = True
        b_obj.draw_bounds_type = bounds_type
        b_obj.game.use_collision_bounds = True
        b_obj.game.collision_bounds_type = bounds_type
        b_obj.game.radius = radius
        b_me = b_obj.data
        if n_obj:
            # todo [pyffi] nif xml 0.7.1.1 HavokMaterial is a union of 3 enums under the HavokMaterial.material field, probably broken!
            #              needs union support on pyffi end
            for mat_type in ("material", "oblivion_havok_material", "fallout_3_havok_material", "skyrim_havok_material"):
                havok_material = getattr(n_obj, mat_type, None)
                if havok_material:
                    if hasattr(havok_material, "material"):
                        # HavokMaterial.material is an enum under the hood
                        # pyffi exposes it as an int (struct.get_basic_attribute) and returns the enum's default value
                        # we treat it as if it was non-basic to get the enum itself
                        mat_enum = havok_material.get_attribute("material")
                        mat_name = str(mat_enum)
                    else:
                        # fallback, not sure if we should do this
                        mat_name = str(havok_material)
                    b_mat = get_material(mat_name)
                    b_me.materials.append(b_mat)

    @staticmethod
    def center_origin_to_matrix(n_center, n_dir):
        """ Helper for capsules to transform nif data into a local matrix """
        # get the rotation that makes (1,0,0) match m_dir
        m_dir = mathutils.Vector((n_dir.x, n_dir.y, n_dir.z)).normalized()
        rot = m_dir.to_track_quat("Z", "Y").to_matrix().to_4x4()
        rot.translation = (n_center.x, n_center.y, n_center.z)
        return rot

    def import_bounding_volume(self, bounding_volume):
        """Imports a NiCollisionData's bounding_volume """

        bvt = bounding_volume.collision_type
        # sphere
        if bvt == 0:
            return self.import_spherebv(bounding_volume.sphere)
        # box
        elif bvt == 1:
            return self.import_boxbv(bounding_volume.box)
        # capsule
        elif bvt == 2:
            return self.import_capsulebv(bounding_volume.capsule)
        # union - a bundle
        elif bvt == 4:
            volumes = []
            for sub_vol in bounding_volume.union.bounding_volumes:
                volumes.extend(self.import_bounding_volume(sub_vol))
            return volumes
        # don't support 5 Half Space for now
        return []

    def import_spherebv(self, sphere):
        r = sphere.radius
        c = sphere.center
        b_obj = Object.box_from_extents("sphere", -r, r, -r, r, -r, r)
        b_obj.location = (c.x, c.y, c.z)
        self.set_b_collider(b_obj, "SPHERE", r)
        return [b_obj]

    def import_boxbv(self, box):
        offset = box.center
        # ignore for now, seems to be a unity 3x3 matrix
        axes = box.axis
        x, y, z = box.extent
        b_obj = Object.box_from_extents("box", -x, x, -y, y, -z, z)
        b_obj.location = (offset.x, offset.y, offset.z)
        self.set_b_collider(b_obj, "BOX", (x + y + z) / 3)
        return [b_obj]

    def import_capsulebv(self, capsule):
        offset = capsule.center
        # always a normalized vector
        direction = capsule.origin
        # nb properly named in newer nif.xmls
        extent = capsule.unknown_float_1
        radius = capsule.unknown_float_2

        # positions of the box verts
        minx = miny = -radius
        maxx = maxy = +radius
        minz = -(extent + 2 * radius) / 2
        maxz = +(extent + 2 * radius) / 2

        # create blender object
        b_obj = Object.box_from_extents("capsule", minx, maxx, miny, maxy, minz, maxz)
        # apply transform in local space
        b_obj.matrix_local = self.center_origin_to_matrix(offset, direction)
        self.set_b_collider(b_obj, "CAPSULE", radius)
        return [b_obj]

    def import_bhk_shape(self, bhkshape):
        """Imports any supported collision shape as list of blender meshes."""

        if isinstance(bhkshape, NifFormat.bhkTransformShape):
            return self.import_bhktransform(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkRigidBody):
            return self.import_bhkridgidbody(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkBoxShape):
            return self.import_bhkbox_shape(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkSphereShape):
            return self.import_bhksphere_shape(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkCapsuleShape):
            return self.import_bhkcapsule_shape(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkConvexVerticesShape):
            return self.import_bhkconvex_vertices_shape(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkPackedNiTriStripsShape):
            return self.import_bhkpackednitristrips_shape(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkNiTriStripsShape):
            self.havok_mat = bhkshape.material
            return reduce(operator.add, (self.import_bhk_shape(strips) for strips in bhkshape.strips_data))

        elif isinstance(bhkshape, NifFormat.NiTriStripsData):
            return self.import_nitristrips(bhkshape)

        elif isinstance(bhkshape, NifFormat.bhkMoppBvTreeShape):
            return self.import_bhk_shape(bhkshape.shape)

        elif isinstance(bhkshape, NifFormat.bhkListShape):
            return reduce(operator.add, (self.import_bhk_shape(subshape) for subshape in bhkshape.sub_shapes))

        NifLog.warn("Unsupported bhk shape {0}".format(bhkshape.__class__.__name__))
        return []

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
            b_col_obj.nifcollision.solver_deactivation = NifFormat.SolverDeactivation._enumkeys[
                bhkshape.solver_deactivation]
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

    def import_bounding_box(self, n_block):
        """Import a NiNode's bounding box or attached BSBound extra data."""
        if not n_block or not isinstance(n_block, NifFormat.NiNode):
            return []
        # we have a ninode with bounding box
        if n_block.has_bounding_box:
            b_name = 'Bounding Box'

            # Ninode's bbox behaves like a seperate mesh.
            # bounding_box center(n_block.bounding_box.translation) is relative to the bound_box
            minx = n_block.bounding_box.translation.x - n_block.translation.x - n_block.bounding_box.radius.x
            miny = n_block.bounding_box.translation.y - n_block.translation.y - n_block.bounding_box.radius.y
            minz = n_block.bounding_box.translation.z - n_block.translation.z - n_block.bounding_box.radius.z
            maxx = n_block.bounding_box.translation.x - n_block.translation.x + n_block.bounding_box.radius.x
            maxy = n_block.bounding_box.translation.y - n_block.translation.y + n_block.bounding_box.radius.y
            maxz = n_block.bounding_box.translation.z - n_block.translation.z + n_block.bounding_box.radius.z
            bbox_center = n_block.bounding_box.translation.as_list()

        # we may still have a BSBound extra data attached to this node
        else:
            for n_extra in n_block.get_extra_datas():
                if isinstance(n_extra, NifFormat.BSBound):
                    b_name = 'BSBound'
                    minx = n_extra.center.x - n_extra.dimensions.x
                    miny = n_extra.center.y - n_extra.dimensions.y
                    minz = n_extra.center.z - n_extra.dimensions.z
                    maxx = n_extra.center.x + n_extra.dimensions.x
                    maxy = n_extra.center.y + n_extra.dimensions.y
                    maxz = n_extra.center.z + n_extra.dimensions.z
                    bbox_center = n_extra.center.as_list()
                    break
            # none was found
            else:
                return []

        # create blender object
        b_obj = Object.box_from_extents(b_name, minx, maxx, miny, maxy, minz, maxz)
        # probably only on NiNodes with BB
        if hasattr(n_block, "flags"):
            b_obj.niftools.objectflags = n_block.flags
        b_obj.location = bbox_center
        self.set_b_collider(b_obj, "BOX", max(maxx, maxy, maxz))
        return [b_obj, ]

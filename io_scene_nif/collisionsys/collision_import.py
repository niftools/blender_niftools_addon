"""This script contains classes to import collision objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2012, NIF File Format Library and Tools contributors.
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
from bpy_extras.io_utils import unpack_list, unpack_face_list
import mathutils

from functools import reduce
import operator

import pyffi
from pyffi.formats.nif import NifFormat
from pyffi.utils.quickhull import qhull3d


class bhkshape_import():
    """Import basic and Havok Collision Shapes"""

    def __init__(self, parent):
        self.nif_common = parent

    def import_bhk_shape(self, bhkshape, upbflags="", bsxflags=2):
        """Imports any supported collision shape as list of blender meshes."""

        if isinstance(bhkshape, NifFormat.bhkTransformShape):
            return self.import_bhktransform(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkRigidBody):
            return self.import_bhkridgidbody(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkBoxShape):
            return self.import_bhkbox_shape(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkSphereShape):
            return self.import_bhksphere_shape(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkCapsuleShape):
            return self.import_bhkcapsule_shape(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkConvexVerticesShape):
            return self.import_bhkconvex_vertices_shape(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkPackedNiTriStripsShape):
            return self.import_bhkpackednitristrips_shape(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkNiTriStripsShape):
            self.havok_mat = bhkshape.material
            return reduce(operator.add,
                          (self.import_bhk_shape(strips)
                           for strips in bhkshape.strips_data))

        elif isinstance(bhkshape, NifFormat.NiTriStripsData):
            return self.import_nitristrips(bhkshape, upbflags, bsxflags)

        elif isinstance(bhkshape, NifFormat.bhkMoppBvTreeShape):
            return self.import_bhk_shape(bhkshape.shape)

        elif isinstance(bhkshape, NifFormat.bhkListShape):
            return reduce(operator.add, ( self.import_bhk_shape(subshape)
                                          for subshape in bhkshape.sub_shapes ))

        self.nif_common.warning("Unsupported bhk shape %s"
                            % bhkshape.__class__.__name__)
        return []


    def import_bhktransform(self, bhkshape, upbflags="", bsxflags=2):
        """Imports a BhkTransform block and applies the transform to the collision object"""

        # import shapes
        collision_objs = self.import_bhk_shape(bhkshape.shape)
        # find transformation matrix
        transform = mathutils.Matrix(bhkshape.transform.as_list())

        # fix scale
        transform.translation = transform.translation * self.nif_common.HAVOK_SCALE

        # apply transform
        for b_col_obj in collision_objs:
            b_col_obj.matrix_local = b_col_obj.matrix_local * transform
            # b_col_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[bhkshape.material]
            # and return a list of transformed collision shapes
        return collision_objs


    def import_bhkridgidbody(self, bhkshape, upbflags="", bsxflags=2):
        """Imports a BhkRigidBody block and applies the transform to the collision objects"""

        # import shapes
        collision_objs = self.import_bhk_shape(bhkshape.shape)

        # find transformation matrix in case of the T version
        if isinstance(bhkshape, NifFormat.bhkRigidBodyT):
            # set rotation
            transform = mathutils.Quaternion([
                bhkshape.rotation.w, bhkshape.rotation.x,
                bhkshape.rotation.y, bhkshape.rotation.z]).to_matrix()
            transform = transform.to_4x4()

            # set translation
            transform.translation = mathutils.Vector(
                    (bhkshape.translation.x * self.nif_common.HAVOK_SCALE,
                     bhkshape.translation.y * self.nif_common.HAVOK_SCALE,
                     bhkshape.translation.z * self.nif_common.HAVOK_SCALE))

            # apply transform
            for b_col_obj in collision_objs:
                b_col_obj.matrix_local = b_col_obj.matrix_local * transform

        # set physics flags and mass
        for b_col_obj in collision_objs:
            ''' What are these used for
            ob.rbFlags = (
                Blender.Object.RBFlags.ACTOR |
                Blender.Object.RBFlags.DYNAMIC |
                Blender.Object.RBFlags.RIGIDBODY |
                Blender.Object.RBFlags.BOUNDS)
            '''
            if bhkshape.mass > 0.0001:
                # for physics emulation
                # (mass 0 results in issues with simulation)
                b_col_obj.game.mass = bhkshape.mass / len(collision_objs)

            b_col_obj.nifcollision.oblivion_layer = NifFormat.OblivionLayer._enumkeys[bhkshape.layer]
            b_col_obj.nifcollision.quality_type = NifFormat.MotionQuality._enumkeys[bhkshape.quality_type]
            b_col_obj.nifcollision.motion_system = NifFormat.MotionSystem._enumkeys[bhkshape.motion_system]
            b_col_obj.nifcollision.bsxFlags = bsxflags
            b_col_obj.nifcollision.upb = upbflags
            # note: also imported as rbMass, but hard to find by users
            # so we import it as a property, and this is also what will
            # be re-exported
            b_col_obj.game.mass = bhkshape.mass / len(collision_objs)
            b_col_obj.nifcollision.col_filter = bhkshape.col_filter

        # import constraints
        # this is done once all objects are imported
        # for now, store all imported havok shapes with object lists
        self.nif_common.havok_objects[bhkshape] = collision_objs

        # and return a list of transformed collision shapes
        return collision_objs


    def import_bhkbox_shape(self, bhkshape, upbflags="", bsxflags=2):
        """Import a BhkBox block as a simple Box collision object"""
        # create box
        minx = -bhkshape.dimensions.x * self.nif_common.HAVOK_SCALE
        maxx = +bhkshape.dimensions.x * self.nif_common.HAVOK_SCALE
        miny = -bhkshape.dimensions.y * self.nif_common.HAVOK_SCALE
        maxy = +bhkshape.dimensions.y * self.nif_common.HAVOK_SCALE
        minz = -bhkshape.dimensions.z * self.nif_common.HAVOK_SCALE
        maxz = +bhkshape.dimensions.z * self.nif_common.HAVOK_SCALE

        b_mesh = bpy.data.meshes.new('box')
        vert_list = {}
        vert_index = 0

        for x in [minx, maxx]:
            for y in [miny, maxy]:
                for z in [minz, maxz]:
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = (x,y,z)
                    vert_list[vert_index] = [x,y,z]
                    vert_index += 1

        faces = [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,0,1,5],[7,6,2,3]]
        face_index = 0

        for x in range(len(faces)):
            b_mesh.faces.add(1)
            b_mesh.faces[-1].vertices_raw = faces[face_index]
            face_index += 1

        # link box to scene and set transform
        b_obj = bpy.data.objects.new('box', b_mesh)
        bpy.context.scene.objects.link(b_obj)

        # set bounds type
        b_obj.draw_type = 'WIRE'
        b_obj.draw_bounds_type = 'BOX'
        b_obj.game.use_collision_bounds = True
        b_obj.game.collision_bounds_type = 'BOX'
        b_obj.game.radius = max(vert.co.length for vert in b_mesh.vertices) # TODO - calc actual radius

        # Recalculate mesh to render correctly
        b_mesh.update()
        b_mesh.calc_normals()

        return [ b_obj ]


    def import_bhksphere_shape(self, bhkshape, upbflags="", bsxflags=2):
        """Import a BhkSphere block as a simple uv-sphere collision object"""

        b_radius = bhkshape.radius * self.nif_common.HAVOK_SCALE

        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=8, size=b_radius)
        b_obj = bpy.context.scene.objects.active

        # set bounds type
        b_obj.draw_type = 'WIRE'
        b_obj.draw_bounds_type = 'SPHERE'
        b_obj.game.use_collision_bounds = True
        b_obj.game.collision_bounds_type = 'SPHERE'
        b_obj.game.radius = bhkshape.radius
        b_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[bhkshape.material]

        # Recalculate mesh to render correctly
        b_mesh = b_obj.data
        b_mesh.update()
        b_mesh.calc_normals()

        return [ b_obj ]


    def import_bhkcapsule_shape(self, bhkshape, upbflags="", bsxflags=2):
        """Import a BhkCapsule block as a simple cylinder collision object"""

        # create capsule mesh
        length = (bhkshape.first_point - bhkshape.second_point).norm()
        minx = miny = -bhkshape.radius * self.nif_common.HAVOK_SCALE
        maxx = maxy = +bhkshape.radius * self.nif_common.HAVOK_SCALE
        minz = -(length + 2*bhkshape.radius) * 3.5
        maxz = +(length + 2*bhkshape.radius) * 3.5

        b_mesh = bpy.data.meshes.new('capsule')
        vert_list = {}
        vert_index = 0

        for x in [minx, maxx]:
            for y in [miny, maxy]:
                for z in [minz, maxz]:
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = (x,y,z)
                    vert_list[vert_index] = [x,y,z]
                    vert_index += 1

        faces = [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]]
        face_index = 0

        for x in range(len(faces)):
            b_mesh.faces.add(1)
            b_mesh.faces[-1].vertices

        # link box to scene and set transform

        """
        vert_index = 0
        for x in [minx,maxx]:
            for y in [miny,maxy]:
                for z in [minz,maxz]:
                    vert_index += 1


        bpy.ops.mesh.primitive_cylinder_add(vertices=vert_index, radius=bhkshape.radius*self.nif_common.HAVOK_SCALE, depth=(length*14))
        b_obj = bpy.context.active_object
        """
        b_obj = bpy.data.objects.new('Capsule', b_mesh)
        bpy.context.scene.objects.link(b_obj)

        # set bounds type
        b_obj.draw_type = 'BOUNDS'
        b_obj.draw_bounds_type = 'CYLINDER'
        b_obj.game.use_collision_bounds = True
        b_obj.game.collision_bounds_type = 'CYLINDER'
        b_obj.game.radius = max(vert.co.length for vert in b_mesh.vertices)
        b_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[bhkshape.material]


        # find transform
        if length > self.nif_common.properties.epsilon:
            normal = (bhkshape.first_point - bhkshape.second_point) / length
            normal = mathutils.Vector((normal.x, normal.y, normal.z))
        else:
            self.nif_common.warning(
                "bhkCapsuleShape with identical points:"
                " using arbitrary axis")
            normal = mathutils.Vector((0, 0, 1))
        minindex = min((abs(x), i) for i, x in enumerate(normal))[1]
        orthvec = mathutils.Vector([(1 if i == minindex else 0)
                                            for i in (0,1,2)])
        vec1 = mathutils.Vector.cross(normal, orthvec)
        vec1.normalize()
        vec2 = mathutils.Vector.cross(normal, vec1)
        # the rotation matrix should be such that
        # (0,0,1) maps to normal
        transform = mathutils.Matrix([vec1, vec2, normal])
        transform.resize_4x4()
        transform[3][0] = 3.5 * (bhkshape.first_point.x + bhkshape.second_point.x)
        transform[3][1] = 3.5 * (bhkshape.first_point.y + bhkshape.second_point.y)
        transform[3][2] = 3.5 * (bhkshape.first_point.z + bhkshape.second_point.z)
        b_obj.matrix_local = transform

        # Recalculate mesh to render correctly
        b_mesh.update()
        b_mesh.calc_normals()

        # return object
        return [ b_obj ]


    def import_bhkconvex_vertices_shape(self, bhkshape, upbflags="", bsxflags=2):
        """Import a BhkConvexVertex block as a convex hull collision object"""

        # find vertices (and fix scale)
        n_vertices, n_triangles = qhull3d(
                                  [ (self.nif_common.HAVOK_SCALE * n_vert.x,
                                     self.nif_common.HAVOK_SCALE * n_vert.y,
                                     self.nif_common.HAVOK_SCALE * n_vert.z)
                                     for n_vert in bhkshape.vertices ])

        # create convex mesh
        b_mesh = bpy.data.meshes.new('convexpoly')

        for n_vert in n_vertices:
            b_mesh.vertices.add(1)
            b_mesh.vertices[-1].co = n_vert

        for n_triangle in n_triangles:
            b_mesh.faces.add(1)
            b_mesh.faces[-1].vertices = n_triangle

        # link mesh to scene and set transform
        b_obj = bpy.data.objects.new('Convexpoly', b_mesh)
        bpy.context.scene.objects.link(b_obj)

        b_obj.show_wire = True
        b_obj.draw_type = 'WIRE'
        b_obj.game.use_collision_bounds = True
        b_obj.game.collision_bounds_type = 'CONVEX_HULL'

        # radius: quick estimate
        b_obj.game.radius = max(vert.co.length for vert in b_mesh.vertices)
        b_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[bhkshape.material]

        # also remove duplicate vertices
        numverts = len(b_mesh.vertices)
        # 0.005 = 1/200

        '''
        numdel = b_mesh.remove_doubles(0.005)
        if numdel:
            self.info(
                "Removed %i duplicate vertices"
                " (out of %i) from collision mesh" % (numdel, numverts))
        '''

        # Recalculate mesh to render correctly
        b_mesh.update()
        b_mesh.calc_normals()

        return [ b_obj ]


    def import_nitristrips(self, bhkshape, upbflags="", bsxflags=2):
        """Import a NiTriStrips block as a Triangle-Mesh collision object"""

        b_mesh = bpy.data.meshes.new('poly')
        # no factor 7 correction!!!
        for n_vert in bhkshape.vertices:
            b_mesh.vertices.add(1)
            b_mesh.vertices[-1].co = (n_vert.x, n_vert.y, n_vert.z)

        for n_triangle in list(bhkshape.get_triangles()):
            b_mesh.faces.add(1)
            b_mesh.faces[-1].vertices = n_triangle

        # link mesh to scene and set transform
        b_obj = bpy.data.objects.new('poly', b_mesh)
        bpy.context.scene.objects.link(b_obj)

        # set bounds type
        b_obj.draw_type = 'WIRE'
        b_obj.draw_bounds_type = 'BOX'
        b_obj.show_wire = True
        b_obj.game.use_collision_bounds = True
        b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
        # radius: quick estimate
        b_obj.game.radius = max(vert.co.length for vert in b_mesh.vertices)
        b_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[self.havok_mat]


        # also remove duplicate vertices
        numverts = len(b_mesh.vertices)
        # 0.005 = 1/200
        '''TODO: FIXME
        numdel = b_mesh.remDoubles(0.005)
        if numdel:
            self.info(
                "Removed %i duplicate vertices"
                " (out of %i) from collision mesh"
                % (numdel, numverts))
        '''

        # Recalculate mesh to render correctly
        b_mesh.update()
        b_mesh.calc_normals()

        return [ b_obj ]

    def import_bhkpackednitristrips_shape(self, bhkshape, upbflags="", bsxflags=2):
        """Import a BhkPackedNiTriStrips block as a Triangle-Mesh collision object"""

        # create mesh for each sub shape
        hk_objects = []
        vertex_offset = 0
        subshapes = bhkshape.sub_shapes

        if not subshapes:
            # fallout 3 stores them in the data
            subshapes = bhkshape.data.sub_shapes

        for subshape_num, subshape in enumerate(subshapes):
            b_mesh = bpy.data.meshes.new('poly:%i' % subshape_num)

            for vert_index in range(vertex_offset, vertex_offset + subshape.num_vertices):
                b_vert = bhkshape.data.vertices[vert_index]
                b_mesh.vertices.add(1)
                b_mesh.vertices[-1].co = (b_vert.x * self.nif_common.HAVOK_SCALE,
                                          b_vert.y * self.nif_common.HAVOK_SCALE,
                                          b_vert.z * self.nif_common.HAVOK_SCALE)

            for hktriangle in bhkshape.data.triangles:
                if ((vertex_offset <= hktriangle.triangle.v_1)
                    and (hktriangle.triangle.v_1
                         < vertex_offset + subshape.num_vertices)):
                    b_mesh.faces.add(1)
                    b_mesh.faces[-1].vertices = [
                                             hktriangle.triangle.v_1 - vertex_offset,
                                             hktriangle.triangle.v_2 - vertex_offset,
                                             hktriangle.triangle.v_3 - vertex_offset]
                else:
                    continue
                # check face normal
                align_plus = sum(abs(x)
                                 for x in ( b_mesh.faces[-1].normal[0] + hktriangle.normal.x,
                                            b_mesh.faces[-1].normal[1] + hktriangle.normal.y,
                                            b_mesh.faces[-1].normal[2] + hktriangle.normal.z ))
                align_minus = sum(abs(x)
                                  for x in ( b_mesh.faces[-1].normal[0] - hktriangle.normal.x,
                                             b_mesh.faces[-1].normal[1] - hktriangle.normal.y,
                                             b_mesh.faces[-1].normal[2] - hktriangle.normal.z ))
                # fix face orientation
                if align_plus < align_minus:
                    b_mesh.faces[-1].vertices = ( b_mesh.faces[-1].vertices[1],
                                                  b_mesh.faces[-1].vertices[0],
                                                  b_mesh.faces[-1].vertices[2] )

            # link mesh to scene and set transform
            b_obj = bpy.data.objects.new('poly%i' % subshape_num, b_mesh)
            bpy.context.scene.objects.link(b_obj)

            # set bounds type
            b_obj.draw_type = 'WIRE'
            b_obj.game.use_collision_bounds = True
            b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
            # radius: quick estimate
            b_obj.game.radius = max(vert.co.length for vert in b_mesh.vertices) * self.nif_common.HAVOK_SCALE
            # set material
            b_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[subshape.material]

            # also remove duplicate vertices
            numverts = len(b_mesh.vertices)
            # 0.005 = 1/200
            # bpy.ops.object.editmode_toggle()
            '''
            b_mesh.remove_doubles(limit=0.005)
            if numdel:
                self.info(
                    "Removed %i duplicate vertices"
                    " (out of %i) from collision mesh"
                    % (numdel, numverts))
            '''

            # Recalculate mesh to render correctly
            b_mesh.update()
            b_mesh.calc_normals()

            vertex_offset += subshape.num_vertices
            hk_objects.append(b_obj)

        return hk_objects

class bound_import():
    """Import a bound box shape"""

    def __init__(self, parent):
        self.nif_common = parent

    def import_bounding_box(self, bbox):
        """Import a bounding box (BSBound, or NiNode with bounding box)."""

        # calculate bounds
        if isinstance(bbox, NifFormat.BSBound):
            b_mesh = bpy.data.meshes.new('BSBound')
            minx = bbox.center.x - bbox.dimensions.x
            miny = bbox.center.y - bbox.dimensions.y
            minz = bbox.center.z - bbox.dimensions.z
            maxx = bbox.center.x + bbox.dimensions.x
            maxy = bbox.center.y + bbox.dimensions.y
            maxz = bbox.center.z + bbox.dimensions.z

        elif isinstance(bbox, NifFormat.NiNode):
            if not bbox.has_bounding_box:
                raise ValueError("Expected NiNode with bounding box.")
            b_mesh = bpy.data.meshes.new('Bounding Box')

            # Ninode's(bbox) behaves like a seperate mesh.
            # bounding_box center(bbox.bounding_box.translation) is relative to the bound_box
            minx = bbox.bounding_box.translation.x - bbox.translation.x - bbox.bounding_box.radius.x
            miny = bbox.bounding_box.translation.y - bbox.translation.y - bbox.bounding_box.radius.y
            minz = bbox.bounding_box.translation.z - bbox.translation.z - bbox.bounding_box.radius.z
            maxx = bbox.bounding_box.translation.x - bbox.translation.x + bbox.bounding_box.radius.x
            maxy = bbox.bounding_box.translation.y - bbox.translation.y + bbox.bounding_box.radius.y
            maxz = bbox.bounding_box.translation.z - bbox.translation.z + bbox.bounding_box.radius.z

        else:
            raise TypeError("Expected BSBound or NiNode but got %s."
                            % bbox.__class__.__name__)

        # create mesh
        for x in [minx, maxx]:
            for y in [miny, maxy]:
                for z in [minz, maxz]:
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = (x,y,z)

        faces = [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]]
        b_mesh.faces.add(len(faces))
        b_mesh.faces.foreach_set("vertices_raw", unpack_face_list(faces))

        # link box to scene and set transform
        if isinstance(bbox, NifFormat.BSBound):
            b_obj = bpy.data.objects.new('BSBound', b_mesh)
        else:
            b_obj = bpy.data.objects.new('Bounding Box', b_mesh)
            # XXX this is set in the import_branch() method
            # ob.matrix_local = mathutils.Matrix(
            #    *bbox.bounding_box.rotation.as_list())
            # ob.setLocation(
            #    *bbox.bounding_box.translation.as_list())

        # set bounds type
        b_obj.show_bounds = True
        b_obj.draw_type = 'BOUNDS'
        b_obj.draw_bounds_type = 'BOX'
        # quick radius estimate
        b_obj.game.radius = max(maxx, maxy, maxz)
        bpy.context.scene.objects.link(b_obj)
        return b_obj

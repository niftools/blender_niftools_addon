"""This script contains helper methods to import/export collision objects."""

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

class shape_import():
    
    def __init__(self, parent):
        self.nif_common = parent

    def import_bhk_shape(self, bhkshape, upbflags="", bsxflags=2):        
        """Imports a collision shape as list of blender meshes."""

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
        # import shapes
        collision_objs = self.import_bhk_shape(bhkshape.shape)
        # find transformation matrix
        transform = mathutils.Matrix(bhkshape.transform.as_list())
        
        # fix scale
        transform.translation = transform.translation * self.nif_common.HAVOK_SCALE

        # apply transform
        for b_col_obj in collision_objs:
            b_col_obj.matrix_local = b_col_obj.matrix_local * transform
            #b_col_obj.nifcollision.havok_material = NifFormat.HavokMaterial._enumkeys[bhkshape.material]
            # and return a list of transformed collision shapes
        return collision_objs
    
    def import_bhkridgidbody(self, bhkshape, upbflags="", bsxflags=2):
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
        b_obj.game.radius = max(vert.co.length for vert in b_mesh.vertices) #todo - calc actual radius
        
        #recalculate to ensure mesh functions correctly
        b_mesh.update()
        b_mesh.calc_normals()
        
        return [ b_obj ]

    def import_bhksphere_shape(self, bhkshape, upbflags="", bsxflags=2):
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
        
        #recalculate to ensure mesh functions correctly
        b_mesh = b_obj.data 
        b_mesh.update()
        b_mesh.calc_normals()
        
        return [ b_obj ]
    
    def import_bhkcapsule_shape(self, bhkshape, upbflags="", bsxflags=2):
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
        
        #recalculate to ensure mesh functions correctly
        b_mesh.update()
        b_mesh.calc_normals()
        
        # return object
        return [ b_obj ]

    def import_bhkconvex_vertices_shape(self, bhkshape, upbflags="", bsxflags=2):
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
        
        #recalculate to ensure mesh functions correctly
        b_mesh.update()
        b_mesh.calc_normals()
                    
        return [ b_obj ]

    def import_nitristrips(self, bhkshape, upbflags="", bsxflags=2):
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
        
        #recalculate to ensure mesh functions correctly
        b_mesh.update()
        b_mesh.calc_normals()
        
        return [ b_obj ]

    def import_bhkpackednitristrips_shape(self, bhkshape, upbflags="", bsxflags=2):
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
            #bpy.ops.object.editmode_toggle()
            '''
            b_mesh.remove_doubles(limit=0.005)
            if numdel:
                self.info(
                    "Removed %i duplicate vertices"
                    " (out of %i) from collision mesh"
                    % (numdel, numverts))
            '''

            #recalculate to ensure mesh functions correctly
            b_mesh.update()
            b_mesh.calc_normals()
            
            vertex_offset += subshape.num_vertices
            hk_objects.append(b_obj)

        return hk_objects

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
            
            #Ninode's(bbox) internal bounding_box behaves like a seperate mesh.
            #bounding_box center(bbox.bounding_box.translation) is relative to the bound_box
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
            #ob.matrix_local = mathutils.Matrix(
            #    *bbox.bounding_box.rotation.as_list())
            #ob.setLocation(
            #    *bbox.bounding_box.translation.as_list())

        # set bounds type
        b_obj.show_bounds = True
        b_obj.draw_type = 'BOUNDS'
        b_obj.draw_bounds_type = 'BOX'
        #quick radius estimate
        b_obj.game.radius = max(maxx, maxy, maxz)
        bpy.context.scene.objects.link(b_obj)
        return b_obj

##Export Section ##
class shape_export():
    
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38
    
    def __init__(self, parent):
        self.nif_common = parent
    
    def export_collision_helper(self, b_obj, parent_block):
        """Helper function to add collision objects to a node. This function
        exports the rigid body, and calls the appropriate function to export
        the collision geometry in the desired format.

        @param b_obj: The object to export as collision.
        @param parent_block: The NiNode parent of the collision.
        """

        # is it packed
        coll_ispacked = (b_obj.game.collision_bounds_type == 'TRIANGLE_MESH')

        # find physics properties/defaults
        n_havok_mat = b_obj.nifcollision.havok_material
        layer = b_obj.nifcollision.oblivion_layer
        motion_system = b_obj.nifcollision.motion_system
        quality_type = b_obj.nifcollision.quality_type
        mass = 1.0 # will be fixed later
        col_filter = b_obj.nifcollision.col_filter
        
        #Aaron1178 collison stuff
        '''
        #export bsxFlags
        self.export_bsx_upb_flags(b_obj, parent_block)
        '''    

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collision_object:
            # note: collision settings are taken from lowerclasschair01.nif
            if b_obj.nifcollision.oblivion_layer == NifFormat.OblivionLayer.OL_BIPED:
                # special collision object for creatures
                n_col_obj = self.nif_common.create_block("bhkBlendCollisionb_object", b_obj)
                n_col_obj.flags = 9
                n_col_obj.unknown_float_1 = 1.0
                n_col_obj.unknown_float_2 = 1.0
                # also add a controller for it
                blendctrl = self.nif_common.create_block("bhkBlendController", b_obj)
                blendctrl.flags = 12
                blendctrl.frequency = 1.0
                blendctrl.phase = 0.0
                blendctrl.start_time = self.FLOAT_MAX
                blendctrl.stop_time = self.FLOAT_MIN
                parent_block.add_controller(blendctrl)
            else:
                # usual collision object
                n_col_obj = self.nif_common.create_block("bhkCollisionObject", b_obj)
                if layer == NifFormat.OblivionLayer.OL_ANIM_STATIC and col_filter != 128:
                    # animated collision requires flags = 41
                    # unless it is a constrainted but not keyframed object
                    n_col_obj.flags = 41
                else:
                    # in all other cases this seems to be enough
                    n_col_obj.flags = 1
                    
            parent_block.collision_object = n_col_obj
            n_col_obj.target = parent_block
            n_col_body = self.nif_common.create_block("bhkRigidBody", b_obj)
            n_col_obj.body = n_col_body
            n_col_body.layer = layer
            n_col_body.col_filter = col_filter
            n_col_body.unknown_5_floats[1] = 3.8139e+36
            n_col_body.unknown_4_shorts[0] = 1
            n_col_body.unknown_4_shorts[1] = 65535
            n_col_body.unknown_4_shorts[2] = 35899
            n_col_body.unknown_4_shorts[3] = 16336
            n_col_body.layer_copy = layer
            n_col_body.unknown_7_shorts[1] = 21280
            n_col_body.unknown_7_shorts[2] = 4581
            n_col_body.unknown_7_shorts[3] = 62977
            n_col_body.unknown_7_shorts[4] = 65535
            n_col_body.unknown_7_shorts[5] = 44
            # mass is 1.0 at the moment (unless property was set)
            # will be fixed later
            n_col_body.mass = mass
            n_col_body.linear_damping = 0.1
            n_col_body.angular_damping = 0.05
            n_col_body.friction = 0.3
            n_col_body.restitution = 0.3
            n_col_body.max_linear_velocity = 250.0
            n_col_body.max_angular_velocity = 31.4159
            n_col_body.penetration_depth = 0.15
            n_col_body.motion_system = motion_system
            n_col_body.unknown_byte_1 = self.nif_common.EXPORT_OB_UNKNOWNBYTE1
            n_col_body.unknown_byte_2 = self.nif_common.EXPORT_OB_UNKNOWNBYTE2
            n_col_body.quality_type = quality_type
            n_col_body.unknown_int_9 = self.nif_common.EXPORT_OB_WIND
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
            
            n_col_mopp = self.nif_common.create_block("bhkMoppBvTreeShape", b_obj)
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
            n_col_shape = self.nif_common.create_block("bhkPackedNiTriStripsShape", b_obj)
            n_col_mopp.shape = n_col_shape
            n_col_shape.unknown_floats[2] = 0.1
            n_col_shape.unknown_floats[4] = 1.0
            n_col_shape.unknown_floats[5] = 1.0
            n_col_shape.unknown_floats[6] = 1.0
            n_col_shape.unknown_floats[8] = 0.1
            n_col_shape.scale = 1.0
            n_col_shape.unknown_floats_2[0] = 1.0
            n_col_shape.unknown_floats_2[1] = 1.0
            
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
            self.nif_common.get_object_matrix(b_obj, 'localspace').as_list())
        rotation = transform.decompose()[1]

        vertices = [vert.co * transform for vert in mesh.vertices]
        triangles = []
        normals = []
        for face in mesh.faces:
            if len(face.vertices) < 3:
                continue # ignore degenerate faces
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
            n_col_shape = self.nif_common.create_block("bhkListShape")
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
            self.warning(
                "Skipping collision object %s without vertices." % b_obj)
            return None
        b_vertlist = [vert.co for vert in b_obj.data.vertices]
        
        minx = min([b_vert[0] for b_vert in b_vertlist])
        miny = min([b_vert[1] for b_vert in b_vertlist])
        minz = min([b_vert[2] for b_vert in b_vertlist])
        maxx = max([b_vert[0] for b_vert in b_vertlist])
        maxy = max([b_vert[1] for b_vert in b_vertlist])
        maxz = max([b_vert[2] for b_vert in b_vertlist])

        if b_obj.game.collision_bounds_type in {'BOX', 'SPHERE'}:
            # note: collision settings are taken from lowerclasschair01.nif
            coltf = self.nif_common.create_block("bhkConvexTransformShape", b_obj)
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
            hktf = mathutils.Matrix(
                self.nif_common.get_object_matrix(b_obj, 'localspace').as_list())
            # the translation part must point to the center of the data
            # so calculate the center in local coordinates
            center = mathutils.Vector(((minx + maxx) / 2.0, (miny + maxy) / 2.0, (minz + maxz) / 2.0))
            # and transform it to global coordinates
            center = center * hktf
            hktf[3][0] = center[0]
            hktf[3][1] = center[1]
            hktf[3][2] = center[2]
            # we need to store the transpose of the matrix
            hktf.transpose()
            coltf.transform.set_rows(*hktf)
            # fix matrix for havok coordinate system
            coltf.transform.m_14 /= self.nif_common.HAVOK_SCALE
            coltf.transform.m_24 /= self.nif_common.HAVOK_SCALE
            coltf.transform.m_34 /= self.nif_common.HAVOK_SCALE

            if b_obj.game.collision_bounds_type == 'BOX':
                colbox = self.nif_common.create_block("bhkBoxShape", b_obj)
                coltf.shape = colbox
                colbox.material = n_havok_mat
                colbox.radius = 0.1
                colbox.unknown_8_bytes[0] = 0x6b
                colbox.unknown_8_bytes[1] = 0xee
                colbox.unknown_8_bytes[2] = 0x43
                colbox.unknown_8_bytes[3] = 0x40
                colbox.unknown_8_bytes[4] = 0x3a
                colbox.unknown_8_bytes[5] = 0xef
                colbox.unknown_8_bytes[6] = 0x8e
                colbox.unknown_8_bytes[7] = 0x3e
                # fix dimensions for havok coordinate system
                colbox.dimensions.x = (maxx - minx) / (2.0 * self.nif_common.HAVOK_SCALE)
                colbox.dimensions.y = (maxy - miny) / (2.0 * self.nif_common.HAVOK_SCALE)
                colbox.dimensions.z = (maxz - minz) / (2.0 * self.nif_common.HAVOK_SCALE)
                colbox.minimum_size = min(colbox.dimensions.x, colbox.dimensions.y, colbox.dimensions.z)
                
            elif b_obj.game.collision_bounds_type == 'SPHERE':
                colsphere = self.nif_common.create_block("bhkSphereShape", b_obj)
                coltf.shape = colsphere
                colsphere.material = n_havok_mat
                # take average radius and
                # Todo find out what this is: fix for havok coordinate system (6 * 7 = 42)
                colsphere.radius = (maxx - minx + maxy - miny + maxz - minz) / (6.0 * self.nif_common.HAVOK_SCALE)

            return coltf

        elif b_obj.game.collision_bounds_type in {'CYLINDER', 'CAPSULE'}:
            # take average radius and calculate end points
            localradius = (maxx + maxy - minx - miny) / 4.0
            transform = mathutils.Matrix(
                self.nif_common.get_object_matrix(b_obj, 'localspace').as_list())
            vert1 = mathutils.Vector( [ (maxx + minx)/2.0,
                                       (maxy + miny)/2.0,
                                       minz + localradius ] )
            vert2 = mathutils.Vector( [ (maxx + minx) / 2.0,
                                       (maxy + miny) / 2.0,
                                       maxz - localradius ] )
            vert1 = vert1 * transform
            vert2 = vert2 * transform

            # check if end points are far enough from each other
            if (vert1 - vert2).length < self.properties.epsilon:
                self.warning(
                    "End points of cylinder %s too close,"
                    " converting to sphere." % b_obj)
                # change type
                b_obj.game.collision_bounds_type = 'SPHERE'
                # instead of duplicating code, just run the function again
                return self.export_collision_object(b_obj, layer, n_havok_mat)
            
            # end points are ok, so export as capsule
            colcaps = self.nif_common.create_block("bhkCapsuleShape", b_obj)
            colcaps.material = n_havok_mat
            colcaps.first_point.x = vert1[0] / self.nif_common.HAVOK_SCALE
            colcaps.first_point.y = vert1[1] / self.nif_common.HAVOK_SCALE
            colcaps.first_point.z = vert1[2] / self.nif_common.HAVOK_SCALE
            colcaps.second_point.x = vert2[0] / self.nif_common.HAVOK_SCALE
            colcaps.second_point.y = vert2[1] / self.nif_common.HAVOK_SCALE
            colcaps.second_point.z = vert2[2] / self.nif_common.HAVOK_SCALE

            # set radius, with correct scale
            size_x = b_obj.scale.x
            size_y = b_obj.scale.y
            size_z = b_obj.scale.z
            #sizex, sizey, sizez = b_obj.getsize()
            colcaps.radius = localradius * (size_x + size_y) * 0.5
            colcaps.radius_1 = colcaps.radius
            colcaps.radius_2 = colcaps.radius
            
            # fix havok coordinate system for radii
            colcaps.radius /= self.nif_common.HAVOK_SCALE
            colcaps.radius_1 /= self.nif_common.HAVOK_SCALE
            colcaps.radius_2 /= self.nif_common.HAVOK_SCALE
            return colcaps

        elif b_obj.game.collision_bounds_type == 'CONVEX_HULL':
            b_mesh = b_obj.data
            b_transform_mat = mathutils.Matrix(
                self.nif_common.get_object_matrix(b_obj, 'localspace').as_list())          
            
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
            fnormlist = [b_rot_quat * b_face.normal for b_face in b_mesh.faces]
            fdistlist = [(b_transform_mat * (-1 * b_mesh.vertices[b_mesh.faces[b_face.index].vertices[0]].co)).dot(
                            b_rot_quat.to_matrix() * b_face.normal)
                         for b_face in b_mesh.faces ]

            # remove duplicates through dictionary
            vertdict = {}
            for i, vert in enumerate(vertlist):
                vertdict[(int(vert[0]*self.nif_common.VERTEX_RESOLUTION),
                          int(vert[1]*self.nif_common.VERTEX_RESOLUTION),
                          int(vert[2]*self.nif_common.VERTEX_RESOLUTION))] = i
            fdict = {}
            for i, (norm, dist) in enumerate(zip(fnormlist, fdistlist)):
                fdict[(int(norm[0]*self.nif_common.NORMAL_RESOLUTION),
                       int(norm[1]*self.nif_common.NORMAL_RESOLUTION),
                       int(norm[2]*self.nif_common.NORMAL_RESOLUTION),
                       int(dist*self.nif_common.VERTEX_RESOLUTION))] = i
            # sort vertices and normals
            vertkeys = sorted(vertdict.keys())
            fkeys = sorted(fdict.keys())
            vertlist = [ vertlist[vertdict[hsh]] for hsh in vertkeys ]
            fnormlist = [ fnormlist[fdict[hsh]] for hsh in fkeys ]
            fdistlist = [ fdistlist[fdict[hsh]] for hsh in fkeys ]

            if len(fnormlist) > 65535 or len(vertlist) > 65535:
                raise NifExportError(
                    "ERROR%t|Too many faces/vertices."
                    " Decimate/split your b_mesh and try again.")
            
            colhull = self.nif_common.create_block("bhkConvexVerticesShape", b_obj)
            colhull.material = n_havok_mat
            colhull.radius = 0.1
            colhull.unknown_6_floats[2] = -0.0 # enables arrow detection
            colhull.unknown_6_floats[5] = -0.0 # enables arrow detection
            # note: unknown 6 floats are usually all 0
            colhull.num_vertices = len(vertlist)
            colhull.vertices.update_size()
            for vhull, vert in zip(colhull.vertices, vertlist):
                vhull.x = vert[0] / self.nif_common.HAVOK_SCALE
                vhull.y = vert[1] / self.nif_common.HAVOK_SCALE
                vhull.z = vert[2] / self.nif_common.HAVOK_SCALE
                # w component is 0
            colhull.num_normals = len(fnormlist)
            colhull.normals.update_size()
            for nhull, norm, dist in zip(colhull.normals, fnormlist, fdistlist):
                nhull.x = norm[0]
                nhull.y = norm[1]
                nhull.z = norm[2]
                nhull.w = dist / self.nif_common.HAVOK_SCALE

            return colhull

        else:
            raise NifExportError(
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
            n_bbox = self.nif_common.create_block("BSBound")
            # ... the following incurs double scaling because it will be added in
            # both the extra data list and in the old extra data sequence!!!
            #block_parent.add_extra_data(n_bbox)
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
            n_bbox = self.nif_common.create_ninode()
            block_parent.add_child(n_bbox)
            # set name, flags, translation, and radius
            n_bbox.name = "Bounding Box"
            n_bbox.flags = 4
            n_bbox.translation.x = (minx + maxx) * 0.5 + b_obj.location[0]
            n_bbox.translation.y = (minx + maxx) * 0.5 + b_obj.location[1]
            n_bbox.translation.z = (minx + maxx) * 0.5 + b_obj.location[2]
            n_bbox.rotation.set_identity()
            n_bbox.has_bounding_box = True
            
            #Ninode's(n_bbox) internal bounding_box behaves like a seperate mesh.
            #bounding_box center(n_bbox.bounding_box.translation) is relative to the bound_box
            n_bbox.bounding_box.translation.deepcopy(n_bbox.translation)
            n_bbox.bounding_box.rotation.set_identity()
            n_bbox.bounding_box.radius.x = (maxx - minx) * 0.5
            n_bbox.bounding_box.radius.y = (maxy - miny) * 0.5
            n_bbox.bounding_box.radius.z = (maxz - minz) * 0.5

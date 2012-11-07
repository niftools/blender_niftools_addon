"""Import and export collision data"""

import bpy
import nose.tools

from test.geometry.test_geometry import TestBaseGeometry
from pyffi.formats.nif import NifFormat

class TestBhkCollision():
    ''' Helper class with common features of Collision Tree'''

    def n_check_bsxflags_property(self, n_data):
        #We check that there is a BSXFlags node. This is regarding collisions.
        #Without a BSXFlags, collisions will not work
        nose.tools.assert_is_instance(n_data, NifFormat.BSXFlags)
        nose.tools.assert_equal(n_data.integer_data, 2) #2 = enable collision flag

    def n_check_upb_property(self, n_data, default = "Mass = 0.000000 Ellasticity = 0.300000 Friction = 0.300000 Unyielding = 0 Simulation_Geometry = 2 Proxy_Geometry = <None> Use_Display_Proxy = 0 Display_Children = 1 Disable_Collisions = 0 Inactive = 0 Display_Proxy = <None> "):
        #We check that there is an NiStringExtraData node and that its name is 'UPB'
        #'UPB' stands for 'User Property Buffer'
        nose.tools.assert_is_instance(n_data, NifFormat.NiStringExtraData)
        nose.tools.assert_equal(n_data.name, b'UPB')

        valuestring = n_data.string_data
        valuestring = valuestring.decode()
        valuestring = valuestring.replace("\r\n"," ")
        UPBString = default
        nose.tools.assert_equal(valuestring, UPBString)

    def n_check_bhkcollisionobject_data(self, n_data):

        #check if n_ninode.collision_object is bhkCollisionObject, not None or other
        nose.assert_is_instance(n_data, NifFormat.bhkCollisionObject)
        #Most Objects collision data flags are 1
        nose.assert_equal(n_data.flags, 1)

    def n_check_bhkrigidbody_data(self, n_data):
        #add code to test lots of lovely things
        pass

    def n_check_bhkrighidbodyt_data(self, n_data):
        #this is inherited from bhkrigidbody, but what is the difference?
        pass

class TestBhkCollisionBoxShape(TestBaseGeometry, TestBhkCollision):
    n_name = "collisions/base_bhkcollision_box" #name of nif
    b_name = "Cube" #name of blender mesh object

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_coll = TestBaseGeometry.b_create_object(self, "CollisionBox")
        b_coll.draw_type = 'WIRE'

        #Physics
        b_coll.game.use_collision_bounds = True
        b_coll.game.collision_bounds_type = 'BOX'

        b_coll.nifcollision.use_blender_properties = True
        b_coll.nifcollision.motion_system = "MO_SYS_FIXED"
        b_coll.nifcollision.oblivion_layer = "OL_STATIC"
        b_coll.nifcollision.quality_type = "MO_QUAL_FIXED"
        b_coll.nifcollision.col_filter = 0
        b_coll.nifcollision.havok_material = "HAV_MAT_WOOD"

        b_coll.select = True

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj

    def b_check_object(self, b_obj):
        self.b_check_geom(b_obj.data)
        self.b_check_collision_data(b_obj)

    def b_check_geom(self, b_mesh):
        pass

    def b_check_collision_data(self, b_obj):
        #We check if the collision settings have been added
        nose.tools.assert_equal(b_obj.game.use_collision_bounds, True)
        nose.tools.assert_equal(b_obj.nifcollision.use_blender_properties, True)
        nose.tools.assert_equal(b_obj.nifcollision.motion_system, "MO_SYS_FIXED")
        nose.tools.assert_equal(b_obj.nifcollision.oblivion_layer, "OL_STATIC")
        nose.tools.assert_equal(b_obj.nifcollision.col_filter, 0)
        nose.tools.assert_equal(b_obj.nifcollision.havok_material, "HAV_MAT_WOOD")

    def n_check_data(self, n_data):
        n_ninode = n_data.roots[0]
        nose.tools.assert_is_instance(n_ninode, NifFormat.NiNode)
        #check that we have the other blocks

        #check to see that n_ninode.num_extra_data_list == 2, so we can execute the methods bellow
        nose.tools.assert_equal(n_ninode.num_extra_data_list, 2)
        self.n_check_bsxflags_property(n_ninode.extra_data_list[0])
        self.n_check_upb_property(n_ninode.extra_data_list[1])

        #execute method below
        self.n_check_bhkboxshape_data(n_ninode.collision_object)
        pass

    def n_check_bhkboxshape_data(self, data):
        nose.tools.assert_is_instance(data.body, NifFormat.bhkRigidBody);
        nose.tools.assert_is_instance(data.body.shape.shape, NifFormat.bhkBoxShape);
        nose.tools.assert_equal(data.body.shape.material, 9);
        pass

class TestBhkCollisionSphereShape(TestBaseGeometry, TestBhkCollision):
    n_name = "collisions/base_bhkcollision_sphere" #name of nif
    b_name = "Cube" #name of blender mesh object

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)

        bpy.ops.mesh.primitive_uv_sphere_add()

        b_coll = bpy.data.objects["Sphere"]
        b_coll.data.show_double_sided = False
        b_coll.name = "CollisionSphere"
        b_coll = bpy.data.objects["CollisionSphere"]
        b_coll.draw_type = 'WIRE'

        #Physics
        b_coll.game.use_collision_bounds = True
        b_coll.game.collision_bounds_type = 'SPHERE'

        b_coll.nifcollision.use_blender_properties = True
        b_coll.nifcollision.motion_system = "MO_SYS_FIXED"
        b_coll.nifcollision.oblivion_layer = "OL_STATIC"
        b_coll.nifcollision.quality_type = "MO_QUAL_FIXED"
        b_coll.nifcollision.col_filer = 0
        b_coll.nifcollision.havok_material = "HAV_MAT_WOOD"

        b_coll.select = True

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj

    def b_check_object(self, b_obj):
        self.b_check_data(self, b_obj)# we double check the base mesh
        self.b_check_collision_data(b_obj)

    def b_check_data(self, b_mesh):
        pass

    def b_check_collision_data(self, b_obj):
        #here we check our blender collision data
        pass

    def n_check_data(self, n_data):
        n_ninode = n_data.roots[0]
        nose.tools.assert_is_instance(n_ninode, NifFormat.NiNode)
        #check that we have the other blocks

        #check to see that n_ninode.num_extra_data_list == 2, so we can execute the methods bellow
        nose.tools.assert_equal(n_ninode.num_extra_data_list,2)
        self.n_check_bsxflags_property(n_ninode.extra_data_list[0])
        self.n_check_upb_property(n_ninode.extra_data_list[1])

        #execute method bellow
        self.n_check_bhksphereshape_data(n_ninode.collision_object)
        pass

    def n_check_bhksphereshape_data(self, data):
        #Check specific block data
        pass

class TestBhkCollisionTriangleShape(TestBaseGeometry, TestBhkCollision):
    n_name = "collisions/base_bhkcollision_triangle" #name of nif
    b_name = "CubeObject" #name of blender mesh object

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self, self.b_name)

        bpy.ops.mesh.primitive_cube_add()

        b_coll = bpy.data.objects["Cube"]
        b_coll.data.show_double_sided = False
        b_coll.name = "CollisionTriangles"
        b_coll = bpy.data.objects["CollisionTriangles"]
        b_coll.draw_type = 'WIRE'

        #Physics
        b_coll.game.use_collision_bounds = True
        b_coll.game.collision_bounds_type = 'TRIANGLE_MESH'

        b_coll.nifcollision.use_blender_properties = True
        b_coll.nifcollision.motion_system = "MO_SYS_FIXED"
        b_coll.nifcollision.oblivion_layer = "OL_STATIC"
        b_coll.nifcollision.quality_type = "MO_QUAL_FIXED"
        b_coll.nifcollision.col_filer = 0
        b_coll.nifcollision.havok_material = "HAV_MAT_WOOD"

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj

    def b_check_data(self, b_obj):
        #TestBaseGeometry.b_check_data(self, b_obj)# we double check the base mesh
        self.b_check_geom(b_obj.data)
        self.b_check_collision_data(b_obj)

    def b_check_geom(self, b_mesh):
        if b_mesh.name == "poly0":
            nose.tools.assert_equal(len(b_mesh.vertices), 8)

    def b_check_collision_data(self, b_obj):
        pass

    def n_check_data(self, n_data):
        n_ninode = n_data.roots[0]
        nose.tools.assert_is_instance(n_ninode, NifFormat.NiNode)
        #check that we have the other blocks

        #check to see that n_ninode.num_extra_data_list == 2, so we can execute the methods bellow
        nose.tools.assert_equal(n_ninode.num_extra_data_list,2)
        self.n_check_bsxflags_property(n_ninode.extra_data_list[0])
        self.n_check_upb_property(n_ninode.extra_data_list[1])

        #execute method bellow
        self.n_check_bhktriangleshape_data(n_ninode.collision_object)
        pass

    def n_check_bhktriangleshape_data(self, data):
        #Check specific block data
        pass

class TestBhkCapsuleObject(TestBaseGeometry, TestBhkCollision):
    n_name = "collisions/base_bhkcollision_capsule" #name of nif
    b_name = "Cube" #name of blender mesh object

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self, self.b_name)

        bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=1.2,depth=2)

        b_coll = bpy.context.active_object
        b_coll.data.show_double_sided = False
        b_coll.name = "CollisionCapsule"
        b_coll = bpy.data.objects["CollisionCapsule"]
        b_coll.draw_type = 'WIRE'

        #Physics
        b_coll.game.use_collision_bounds = True
        b_coll.game.collision_bounds_type = 'CAPSULE'

        b_coll.nifcollision.use_blender_properties = True
        b_coll.nifcollision.motion_system = "MO_SYS_FIXED"
        b_coll.nifcollision.oblivion_layer = "OL_STATIC"
        b_coll.nifcollision.quality_type = "MO_QUAL_FIXED"
        b_coll.nifcollision.col_filer = 0
        b_coll.nifcollision.havok_material = "HAV_MAT_WOOD"

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj

    def b_check_data(self, b_obj):
        #TestBaseGeometry.b_check_data(self, b_obj)# we double check the base mesh
        self.b_check_geom(b_obj.data)
        self.b_check_collision_data(b_obj)

    def b_check_geom(self, b_mesh):
        pass

    def b_check_collision_data(self, b_obj):
        pass

    def n_check_data(self, n_data):
        n_ninode = n_data.roots[0]
        nose.tools.assert_is_instance(n_ninode, NifFormat.NiNode)
        #check that we have the other blocks

        #check to see that n_ninode.num_extra_data_list == 2, so we can execute the methods bellow
        nose.tools.assert_equal(n_ninode.num_extra_data_list,2)
        self.n_check_bsxflags_property(n_ninode.extra_data_list[0])
        self.n_check_upb_property(n_ninode.extra_data_list[1])

        #execute method bellow
        self.n_check_bhkcapsuleshape_data(n_ninode.collision_object)
        pass

    def n_check_bhkcapsuleshape_data(self, data):
        #Check specific block data
        pass


'''
class TestBhkCollisionCapsule(TestBaseGeometry, TestBhkCollision):
'''
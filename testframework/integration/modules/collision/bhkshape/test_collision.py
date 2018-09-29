"""Import and export collision data"""
import  bpy

import nose

from integration import SingleNif
from integration.modules.collision import bhkshape
from integration.modules.object import b_gen_object


class TestBhkCollisionSphereShape(SingleNif):
    n_name = "collisions/base_bhkcollision_sphere"  # name of nif
    b_name = "Cube"  # name of blender mesh object

    def b_create_object(self):
        b_obj = b_gen_object.b_create_object(self)

        self.b_create_collision_sphere()

    def b_create_collision_sphere(self):
        bpy.ops.mesh.primitive_uv_sphere_add()
        b_coll = bpy.data.objects["Sphere"]
        b_coll.data.show_double_sided = False
        b_coll.name = "CollisionSphere"
        b_coll = bpy.data.objects["CollisionSphere"]


class TestBhkCollisionTriangleShape(SingleNif):
    g_path = bhkshape.G_PATH
    g_name = "base_bhkcollision_triangle"  # name of nif
    b_name = "CubeObject"  # name of blender mesh object

    def b_create_object(self):
        b_obj = b_gen_object.b_create_object(self, self.b_name)

        self.b_create_collision_triangles()

    def b_create_collision_triangles(self):
        bpy.ops.mesh.primitive_cube_add()
        b_coll = bpy.data.objects["Cube"]
        b_coll.data.show_double_sided = False
        b_coll.name = "CollisionTriangles"
        b_coll = bpy.data.objects["CollisionTriangles"]

    def b_check_geom(self, b_mesh):
        if b_mesh.name == "poly0":
            nose.tools.assert_equal(len(b_mesh.vertices), 8)


class TestBhkCapsuleObject(SingleNif):

    g_path = bhkshape.G_PATH  # name of nif
    g_name = "base_bhkcollision_capsule"  # name of nif
    b_name = "Cube"  # name of blender mesh object

    def b_create_object(self):
        b_obj = b_gen_object.b_create_object(self, self.b_name)

        self.b_create_collision_cylider()

    def b_create_collision_cylider(self):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.2, depth=2)
        b_coll = bpy.context.active_object
        b_coll.data.show_double_sided = False
        b_coll.name = "CollisionCapsule"
        b_coll = bpy.data.objects["CollisionCapsule"]
        b_coll.draw_type = 'WIRE'

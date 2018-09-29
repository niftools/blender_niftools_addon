"""Export and import bound meshes."""

import bpy
import nose.tools

from integration import SingleNif
from integration.data import n_gen_header, b_gen_header
from integration.modules.collision.bounds import n_gen_boundbox


class TestBBox(SingleNif):
    g_path = "collisions/boundbox"
    g_name = "test_bounding_box"
    b_name = "Bounding Box"

    b_verts = {
        (10, 10, -10),
        (-10, 10, 10),
        (10, -10, -10),
        (-10, -10, 10),
        (-10, -10, -10),
        (-10, 10, -10),
        (10, 10, 10),
        (10, -10, 10),
    }

    def b_create_header(self):
        b_gen_header.b_create_morrowind_info()

    def n_create_header(self):
        n_gen_header.n_create_header_morrowind(self.n_data)

    def b_create_data(self):
        # TODO [object] Create base geom
        # b_obj = self.b_create_base_geometry()
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects[bpy.context.active_object.name]
        for vert in b_obj.data.vertices:
            vert.co *= 10
        b_obj.name = self.b_name
        b_obj.show_bounds = True
        # the following are optional
        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'
        b_obj.data.show_double_sided = False

    def n_create_data(self):
        return n_gen_boundbox.n_create_data()

    def b_check_data(self):
        b_bbox = bpy.data.objects[self.b_name]
        nose.tools.assert_true(b_bbox.show_bounds)
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')
        verts = {tuple(round(x, 4) for x in vert.co) for vert in b_bbox.data.vertices}
        nose.tools.assert_set_equal(verts, self.b_verts)

    def n_check_data(self):
        n_bbox = self.n_data.roots[0].children[0]
        nose.tools.assert_equal(n_bbox.has_bounding_box, True)
        nose.tools.assert_almost_equal(n_bbox.bounding_box.radius.x, 10, places=4)
        nose.tools.assert_almost_equal(n_bbox.bounding_box.radius.y, 10, places=4)
        nose.tools.assert_almost_equal(n_bbox.bounding_box.radius.z, 10, places=4)


'''
class TestBSBound(TestBaseGeometry):
    n_name = "collisions/boundbox/bsbound"
    b_name = "BSBound"

    def b_create_data(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_obj.name = self.b_name

        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'

        return b_obj



    def b_check_data(self):
        pass


        b_bbox = b_obj[b_name]
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')


    def n_check_data(self, n_data):
        pass


        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(bbox.has_bounding_box, True)

'''

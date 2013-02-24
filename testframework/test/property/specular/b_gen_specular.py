import nose
import bpy

def b_create_alter_specular_property(b_mat):
    b_mat.specular_color = (0.5, 0.0, 0.0)
    b_mat.specular_intensity = 1.0
        
def b_check_specular_property(b_mat):
    nose.tools.assert_equal(b_mat.specular_color.r, 0.5)
    nose.tools.assert_equal(b_mat.specular_color.g, 0.0)
    nose.tools.assert_equal(b_mat.specular_color.b, 0.0)
    nose.tools.assert_equal(b_mat.specular_intensity, 1.0)
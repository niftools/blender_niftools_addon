import bpy
import nose

def b_create_set_alpha_property(b_mat):
    b_mat.use_transparency = True
    b_mat.alpha = 0.5
    b_mat.transparency_method = 'Z_TRANSPARENCY'
    
def b_check_alpha_property(b_mat):
    '''Check alpha related properties'''
    nose.tools.assert_equal(b_mat.use_transparency, True)
    nose.tools.assert_equal(b_mat.alpha, 0.5)
    nose.tools.assert_equal(b_mat.transparency_method, 'Z_TRANSPARENCY')
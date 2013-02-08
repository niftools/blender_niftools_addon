import bpy
import nose

def b_create_material_block(b_obj):
    b_mat = bpy.data.materials.new(name='Material')
    b_obj.data.materials.append(b_mat)
    bpy.ops.object.shade_smooth()
    return b_mat
    
   
def b_create_set_material_property(b_mat):
    b_mat.diffuse_color = (1.0, 1.0, 1.0) # default - (0.8, 0.8, 0.8)
    b_mat.diffuse_intensity = 1.0 # default - 0.8
    b_mat.specular_intensity = 0.0 # disable NiSpecularProperty
    return b_mat

def b_check_material_block(b_obj):
    '''Check that we have a material'''
    
    b_mesh = b_obj.data
    b_mat = b_mesh.materials[0]
    nose.tools.assert_equal(len(b_mesh.materials), 1)
    return b_mat

def b_check_material_property(b_mat):
    '''Check material has the correct properties'''
    
    nose.tools.assert_equal(b_mat.ambient, 1.0)
    nose.tools.assert_equal(b_mat.diffuse_color[0], 1.0)
    nose.tools.assert_equal(b_mat.diffuse_color[1], 1.0)
    nose.tools.assert_equal(b_mat.diffuse_color[2], 1.0)
    nose.tools.assert_equal(b_mat.specular_intensity, 0.0)
import bpy
import math
import mathutils

import nose

def b_create_diffuse_textureslot(b_mat):
    b_mat_texslot = b_mat.texture_slots.create(0) # create material texture slot
    b_mat_texslot.texture = bpy.data.textures.new(name='DiffuseTexture', type='IMAGE') # create texture holder
    return b_mat_texslot
    
def b_create_load_texture(b_mat_texslot, texture_path):
    b_mat_texslot.texture.image = bpy.data.images.load(texture_path)
    b_mat_texslot.use = True
    b_mat_texslot.texture_coords = 'UV'
    b_mat_texslot.uv_layer = 'UVMap'
    
def b_create_diffuse_texture_properties(b_mat_texslot):
    b_mat_texslot.use_map_color_diffuse = True
    
def b_check_texture_slot(b_mat):

    nose.tools.assert_equal(b_mat.texture_slots[0] != None, True) # check slot exists
    b_mat_texslot = b_mat.texture_slots[0]
    nose.tools.assert_equal(b_mat_texslot.use, True) # check slot enabled
    self.b_check_texture_property(b_mat_texslot)

def b_check_texture_property(self, b_mat_texslot):
    nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture)
    #nose.tools.assert_equal(b_mat_texslot.texture.image.filepath, self.diffuse_texture_path)
    nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
    nose.tools.assert_equal(b_mat_texslot.uv_layer, 'UVMap')
    nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, True)

   
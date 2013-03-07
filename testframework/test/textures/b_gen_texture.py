from os import path

import bpy
import math
import mathutils

import nose

def b_create_diffuse_textureslot(b_mat):
    b_mat_texslot = b_mat.texture_slots.create(0) # create material texture slot
    b_mat_texslot.texture = bpy.data.textures.new(name='DiffuseTexture', type='IMAGE') # create texture holder
    return b_mat_texslot
    
def b_create_load_texture(b_mat_texslot, abs_text_path):
    b_mat_texslot.texture.image = bpy.data.images.load(abs_text_path)
    b_mat_texslot.use = True
    b_mat_texslot.texture_coords = 'UV'
    b_mat_texslot.uv_layer = 'UVMap'
    
def b_create_diffuse_texture_properties(b_mat_texslot):
    b_mat_texslot.use_map_color_diffuse = True
    
def b_check_texture_slot(b_mat_texslot):
    nose.tools.assert_equal(b_mat_texslot.use, True) # check slot enabled
    nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
    nose.tools.assert_equal(b_mat_texslot.uv_layer, 'UVMap')
    
def b_check_image_texture_property(b_mat_texslot, texture_path):
    
    nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture) #check we have a texture

    n_split_path = texture_path.split(path.sep)
    n_rel_path = n_split_path[len(n_split_path)-3:] #get a path relative to \\textures folder
    
    b_split_path = b_mat_texslot.texture.image.filepath
    b_split_path = b_split_path.split(path.sep) #see if nif loaded correct path
    b_rel_path = b_split_path[len(b_split_path)-3:]
    
    nose.tools.assert_equal(b_rel_path, n_rel_path) #see if we have the right images
    
def b_check_diffuse_texture_settings(b_mat_texslot):
    nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, True)

   
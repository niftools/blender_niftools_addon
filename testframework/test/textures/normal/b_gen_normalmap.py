from os import path

import bpy
import math
import mathutils

import nose

def b_create_normal_texture_properties(b_mat_texslot):
    '''Sets the textureslot settings for using a normal map'''
    
    #Inflence mapping
    b_mat_texslot.use_map_color_diffuse = False
    b_mat_texslot.texture.use_normal_map = True

    #Influence
    
    b_mat_texslot.use_map_normal = True

    
def b_check_normal_texture_settings(b_mat_texslot):
    '''Test the textureslot for settings to use a normal map'''
    
    nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, False)
    nose.tools.assert_equal(b_mat_texslot.texture.use_normal_map, True)
    nose.tools.assert_equal(b_mat_texslot.texture.use_alpha, False)


    nose.tools.assert_equal(b_mat_texslot.use_normal_map, True)